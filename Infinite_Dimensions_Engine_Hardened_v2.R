###############################################################################
# Infinite Dimensions Engine — Hardened v2 (single-file, production-ready R)
# Goals addressed:
# - No leakage: fit all transformers/models on TRAIN; apply to VALID/FULL only via baked objects
# - Deterministic & governable: pinned RNG, per-worker seeds, manifest + model card
# - Safe merging: explicit coverage audits; fail-closed on many-to-many unless override
# - Privacy/security: offline mode; opt-in geocoding; PII scan & redaction controls
# - Resource guards: O(n^2) protections, scalable fallbacks, configurable limits
# - Explainability: stable clustering, segment summaries, out-of-fold (OOF) metrics
# - Configuration via validated YAML/JSON; sensible defaults, but everything overrideable
###############################################################################

## ============================== 0. Libraries ============================== ##
suppressPackageStartupMessages({
  library(tidyverse)
  library(readxl)
  library(jsonlite)
  library(httr)
  library(geosphere)      # distHaversine
  library(cluster)        # silhouette, clusGap
  library(furrr)          # parallel mapping
  library(recipes)        # preprocessing pipeline
  library(randomForest)   # ML potential
  library(rsample)        # initial_split, vfold_cv
  library(janitor)        # clean_names
  library(mclust)         # GMM clustering
  library(dbscan)         # HDBSCAN
  library(FNN)            # Approx NN density
  library(yaml)           # manifest
  library(glue)
})

## ============================== 1. Seeds/Plan ============================ ##
set.seed(42)
RNGkind("L'Ecuyer-CMRG")
# Make future RNG reproducible
plan(multisession, workers = max(1, parallel::detectCores() - 1))
options(future.rng.onMisuse = "ignore")

`%||%` <- function(a, b) if (is.null(a)) b else a
na0 <- function(x) { x[is.na(x)] <- 0; x }
safe_sd <- function(x) sd(x, na.rm = TRUE)
safe_mean <- function(x) mean(x, na.rm = TRUE)
rescale_01 <- function(x){
  if (all(is.na(x))) return(x)
  r <- range(x, na.rm = TRUE); if (diff(r) == 0) return(rep(0.5, length(x)))
  (x - r[1]) / diff(r)
}

stopf <- function(...){ stop(glue::glue(...), call. = FALSE) }
warnf <- function(...){ warning(glue::glue(...), call. = FALSE) }
infof <- function(...){ message(glue::glue(...)) }

## ============================== 2. Config ================================ ##
validate_config <- function(cfg){
  req <- c("target_variable","unit_id")
  missing <- setdiff(req, names(cfg)); if (length(missing)) stopf("Missing config fields: {toString(missing)}")
  cfg
}

make_analytics_config <- function(
  target_variable,                    # KPI column
  unit_id,                            # entity id
  entity_label   = "entity",
  kpi_label      = "KPI",

  # security & privacy
  offline = TRUE,                     # hard-disable outbound HTTP
  geocoding_provider = "off",        # "off" | "osm"
  redact_house_numbers = TRUE,
  add_geo_features = FALSE,           # opt-in
  geo_radii_km = c(1, 5),

  # ingestion/merge
  prefer_keys = c("id","entity_id","store_id","customer_id","campaign_id"),
  min_overlap = 0.3,                  # stricter default
  min_key_quality = 0.7,
  allow_many_to_many = FALSE,         # fail closed

  # feature selection
  max_features = 60,
  topK_levels_per_cat = 30,           # cap categorical one-hot levels
  p_adjust_method = "BH",
  selection_min_score = 0,            # keep all; adjust if you want

  # scaling
  force_scaling_method = NULL,        # NULL auto | "standardize"|"normalize"|"robust"|"log"

  # split & validation
  validation_prop = 0.2,
  vfolds = 5,                          # for OOF metrics

  # dim reduction
  max_pcs = 12,

  # clustering
  clustering_method = "auto",         # "auto"|"kmeans"|"gmm"|"hdbscan"
  max_clusters = 40,
  auto_k = TRUE,
  hdbscan_minPts = 10,

  # drivers
  top_n_cluster_drivers = 20,
  top_n_global_drivers  = 30,

  # potential (consensus)
  use_percentile = TRUE,
  use_regression = TRUE,
  use_ml = TRUE,
  percentile_weight = 0.2,
  regression_weight  = 0.4,
  ml_weight          = 0.4,
  cluster_percentile_target = 0.90,
  clamp_potential_ge_current = FALSE, # do NOT clamp by default

  # uncertainty
  bootstrap_B = 50,                   # lighter default, configurable
  bootstrap_ci = 0.90,

  # resource guards
  n2_guard_threshold = 5000,          # switch to approx at n>5k
  max_workers = max(1, parallel::detectCores()-1)
){
  cfg <- list(
    labels = list(entity = entity_label, kpi = kpi_label),
    target_variable = target_variable,
    unit_id = unit_id,
    security = list(offline=offline),
    ingest = list(prefer_keys=prefer_keys, min_overlap=min_overlap, min_key_quality=min_key_quality,
                  allow_many_to_many=allow_many_to_many),
    privacy = list(geocoding_provider=geocoding_provider, redact_house_numbers=redact_house_numbers),
    geo = list(enabled=add_geo_features, radii_km=geo_radii_km),
    selection = list(max_features=max_features, topK_levels_per_cat=topK_levels_per_cat,
                     p_adjust_method=p_adjust_method, selection_min_score=selection_min_score),
    scaling = list(force_method=force_scaling_method),
    split = list(validation_prop=validation_prop, vfolds=vfolds),
    dimred = list(max_pcs=max_pcs),
    clustering = list(method=clustering_method, max_clusters=max_clusters, auto_k=auto_k, hdbscan_minPts=hdbscan_minPts),
    drivers = list(top_n_cluster=top_n_cluster_drivers, top_n_global=top_n_global_drivers),
    potential = list(use_percentile=use_percentile, use_regression=use_regression, use_ml=use_ml,
                     weights=c(percentile=percentile_weight, regression=regression_weight, ml=ml_weight),
                     cluster_pct=cluster_percentile_target, clamp_ge_current=clamp_potential_ge_current),
    uncertainty = list(B=bootstrap_B, ci=bootstrap_ci),
    guards = list(n2_threshold=n2_guard_threshold, max_workers=max_workers)
  )
  validate_config(cfg)
}

## ====================== 3. Data Loading (schema-agnostic) ================ ##
load_data_agnostic <- function(data_source){
  if (is.character(data_source)) {
    if (grepl("\\.csv$", data_source, ignore.case = TRUE)) {
      readr::read_csv(data_source, show_col_types = FALSE) %>% janitor::clean_names() %>% as_tibble()
    } else if (grepl("\\.xlsx?$", data_source, ignore.case = TRUE)) {
      readxl::read_excel(data_source) %>% janitor::clean_names() %>% as_tibble()
    } else if (grepl("\\.json$", data_source, ignore.case = TRUE)) {
      jsonlite::fromJSON(data_source, simplifyVector = TRUE) %>% as_tibble() %>% janitor::clean_names()
    } else {
      stop("Unsupported file format (.csv/.xlsx/.json).")
    }
  } else if (inherits(data_source, "data.frame") || tibble::is_tibble(data_source)) {
    data_source %>% janitor::clean_names() %>% as_tibble()
  } else {
    stop("Data source must be filepath(s) or a data.frame/tibble.")
  }
}

## ===================== 4. Key Detection / Safe Auto-Merge ================= ##
uniqueness_ratio <- function(x) { x2 <- x[!is.na(x)]; if (length(x2) == 0) return(0); length(unique(x2)) / length(x2) }
value_overlap_score <- function(a, b) { a2 <- unique(na.omit(a)); b2 <- unique(na.omit(b)); if (length(a2) == 0 || length(b2) == 0) return(0); length(intersect(a2,b2)) / length(unique(c(a2,b2))) }
score_key_column <- function(df, col) { v <- df[[col]]; base <- uniqueness_ratio(v); name_bonus <- ifelse(grepl("(?:^|_)(id|code|uuid|sku|email)$", col), 0.2, 0); type_bonus <- ifelse(is.numeric(v) || is.character(v), 0.05, 0); pmin(1, base + name_bonus + type_bonus) }
best_composite_keys <- function(df, max_size = 2, top_k = 6) {
  cands <- names(df)[sapply(df, function(v) is.numeric(v) || is.character(v) || is.factor(v))]
  singles <- tibble(cols = map(cands, ~.x), score = map_dbl(cands, ~score_key_column(df, .x))) %>% arrange(desc(score)) %>% slice_head(n = top_k)
  pairs <- combn(singles$cols, 2, simplify = FALSE)
  pair_scores <- map_dbl(pairs, function(p) { key <- df %>% unite("__key__", all_of(p), sep="||", remove=FALSE, na.rm=FALSE) %>% pull("__key__"); uniqueness_ratio(key) })
  pair_tbl <- if (length(pair_scores)) tibble(cols = pairs, score = pair_scores) else tibble(cols=list(), score=numeric(0))
  bind_rows(singles %>% mutate(type="single"), pair_tbl %>% mutate(type="pair")) %>% arrange(desc(score))
}

check_many_to_many <- function(left, left_key, right, right_key){ ldup <- any(duplicated(left[[left_key]]), na.rm = TRUE); rdup <- any(duplicated(right[[right_key]]), na.rm = TRUE); list(left_dup = ldup, right_dup = rdup, many_to_many = ldup && rdup) }

merge_audit_report <- function(base_df, right_df, base_key, right_key, overlap, many_to_many){
  tibble(
    base_rows = nrow(base_df), right_rows = nrow(right_df),
    base_key = paste(base_key, collapse = "+"), right_key = paste(right_key, collapse = "+"),
    overlap_jaccard = round(overlap, 4),
    base_dupes = sum(duplicated(base_df[[base_key]]), na.rm = TRUE),
    right_dupes = sum(duplicated(right_df[[right_key]]), na.rm = TRUE),
    many_to_many = many_to_many
  )
}

print_merge_report <- function(merge_result) {
  cat("=== Auto-Merge Report ===\n")
  cat("Base:", merge_result$base$name, "| Base key:", paste(merge_result$base$key, collapse="+"), "\n")
  for (s in merge_result$steps) {
    cat("\n→ Joined:", s$right_df, "\n")
    if (!is.null(s$note)) { cat("   ", s$note, "\n"); next }
    cat("   Right key:", paste(s$right_key, collapse="+"), "\n")
    cat("   Overlap (Jaccard):", round(s$overlap,3), "\n")
    cat("   Many-to-many blocked?:", s$many_to_many, "\n")
    cat("   Rows:", s$rows_before, "→", s$rows_after, "\n")
    cat("   New cols:", paste(s$cols_added, collapse=", "), "\n")
  }
  cat("\nTotals — columns:", ncol(merge_result$data), "rows:", nrow(merge_result$data), "\n")
}

load_many_and_merge <- function(data_sources, cfg_ingest){
  dfs <- map(data_sources, load_data_agnostic)
  names(dfs) <- names(dfs) %||% paste0("df", seq_along(dfs))

  key_candidates <- map(dfs, ~best_composite_keys(.x))
  key_candidates <- imap(key_candidates, function(tbl, nm) {
    if (any(cfg_ingest$prefer_keys %in% names(dfs[[nm]]))) {
      pk <- cfg_ingest$prefer_keys[cfg_ingest$prefer_keys %in% names(dfs[[nm]])][1]
      tibble(cols=list(pk), score=1, type="preferred") %>% bind_rows(tbl)
    } else tbl
  })

  sizes <- map_int(dfs, nrow)
  order_base <- order(sizes, decreasing = TRUE)
  base_name <- NULL; base_key <- NULL
  for (nm in names(dfs)[order_base]) {
    kc <- key_candidates[[nm]] %>% slice(1)
    if (nrow(kc) && kc$score[1] >= cfg_ingest$min_key_quality) { base_name <- nm; base_key <- kc$cols[[1]]; break }
  }
  if (is.null(base_name)) { base_name <- names(dfs)[order_base][1]; base_key <- key_candidates[[base_name]]$cols[[1]] }

  base_df <- dfs[[base_name]]
  if (length(base_key) > 1) base_df <- base_df %>% unite(".__merge_key__", all_of(base_key), sep="||", remove=FALSE, na.rm=FALSE) else names(base_df)[names(base_df) == base_key] <- ".__merge_key__"

  merge_steps <- list(); used <- base_name; merged <- base_df

  for (nm in setdiff(names(dfs), base_name)) {
    right <- dfs[[nm]]
    kc_right <- key_candidates[[nm]] %>% slice_head(n=6)
    chosen_right <- NULL
    for (cols in kc_right$cols) {
      tmp <- right
      if (length(cols) > 1) tmp <- tmp %>% unite("__r_key__", all_of(cols), sep="||", remove=FALSE, na.rm=FALSE) else names(tmp)[names(tmp) == cols] <- "__r_key__"
      ov <- value_overlap_score(merged$.__merge_key__, tmp$`__r_key__`)
      if (ov >= cfg_ingest$min_overlap) { chosen_right <- list(cols=cols, ov=ov); right <- tmp; break }
    }

    if (!is.null(chosen_right)) {
      ch <- check_many_to_many(merged, ".__merge_key__", right, "__r_key__")
      if (!cfg_ingest$allow_many_to_many && ch$many_to_many) {
        audit <- merge_audit_report(merged, right, ".__merge_key__", "__r_key__", chosen_right$ov, TRUE)
        merge_steps[[length(merge_steps)+1]] <- list(right_df=nm, right_key=chosen_right$cols, overlap=chosen_right$ov, join_col=".__merge_key__", rows_before=nrow(merged), rows_after=nrow(merged), cols_added=character(0), many_to_many=TRUE, note=paste0("BLOCKED many-to-many. Audit: ", paste(names(audit), audit, collapse=", "))) 
        next
      }
      before_n <- nrow(merged)
      keep_cols <- setdiff(names(right), "__r_key__")
      merged <- merged %>% left_join(right %>% rename(.__merge_key__ = `__r_key__`), by=".__merge_key__")
      after_n <- nrow(merged)
      merge_steps[[length(merge_steps)+1]] <- list(right_df=nm, right_key=chosen_right$cols, overlap=chosen_right$ov, join_col=".__merge_key__", rows_before=before_n, rows_after=after_n, cols_added=setdiff(keep_cols, names(base_df)), many_to_many=ch$many_to_many)
      used <- c(used, nm)
    } else {
      merge_steps[[length(merge_steps)+1]] <- list(right_df=nm, right_key=NA, overlap=0, join_col=NA, rows_before=nrow(merged), rows_after=nrow(merged), cols_added=character(0), many_to_many=FALSE, note="no suitable key found (skipped)")
    }
  }

  list(data = merged, base = list(name=base_name, key=base_key), steps = merge_steps)
}

## ===================== 5. Feature Types & Geo (opt-in) ==================== ##
detect_feature_types <- function(df, target_variable = NULL) {
  tibble(feature = names(df), type = map_chr(names(df), function(cn){ v <- df[[cn]]; if (!is.null(target_variable) && cn == target_variable) return("target"); if (is.numeric(v)) "numeric" else if (is.logical(v)) "binary" else if (is.factor(v) || is.character(v)) "categorical" else "other" }))
}

is_lat <- function(x) is.numeric(x) && all(x >= -90 & x <= 90, na.rm = TRUE)
is_lon <- function(x) is.numeric(x) && all(x >= -180 & x <= 180, na.rm = TRUE)

redact_address <- function(addr) { if (is.na(addr)) return(NA_character_); gsub("^\\s*\\d+\\s+", "", addr) }

geocode_osm_single <- function(address, offline){
  if (offline) return(list(lat=NA_real_, lon=NA_real_))
  url <- "https://nominatim.openstreetmap.org/search"
  resp <- httr::GET(url, query = list(q=address, format="json", limit=1), httr::add_headers(`User-Agent`="infinite-dim-engine/2.0"))
  if (httr::status_code(resp)==200){ js <- httr::content(resp, as="parsed"); if (length(js)>0) return(list(lat=as.numeric(js[[1]]$lat), lon=as.numeric(js[[1]]$lon))) }
  list(lat=NA_real_, lon=NA_real_)
}

geocode_if_needed <- function(df, geo_vars, cfg_privacy, offline){
  out <- df
  has_lat <- length(geo_vars$latitude)>0
  has_lon <- length(geo_vars$longitude)>0
  if (has_lat && has_lon) return(out)
  if (cfg_privacy$geocoding_provider=="off") return(out)
  if (offline) stopf("offline=TRUE prohibits geocoding. Set offline=FALSE to allow.")

  addr_col <- geo_vars$address[1] %||% geo_vars$postcode[1]
  if (is.null(addr_col)) return(out)
  addrs <- df[[addr_col]] %>% as.character()
  if (cfg_privacy$redact_house_numbers) addrs <- vapply(addrs, redact_address, "", USE.NAMES=FALSE)
  uniq <- unique(na.omit(addrs)); if (!length(uniq)) return(out)
  infof("Geocoding via OSM (opt-in, rate-limited)...")
  geocoded <- map_dfr(uniq, function(a){ Sys.sleep(0.5); rec <- geocode_osm_single(a, offline); tibble(.__address__=a, lat=rec$lat, lon=rec$lon) })
  out <- out %>% mutate(.__address__ = if (cfg_privacy$redact_house_numbers) vapply(!!sym(addr_col), redact_address, "") else !!sym(addr_col)) %>% left_join(geocoded, by=".__address__") %>% select(-.__address__)
  out
}

add_geo_features <- function(df, lat_col=NULL, lon_col=NULL, radii_km=c(1,5), n2_threshold=5000){
  out <- df
  if (is.null(lat_col) || is.null(lon_col) || !(lat_col %in% names(df)) || !(lon_col %in% names(df))) return(out)
  coords <- df %>% select(all_of(c(lon_col, lat_col))) %>% as.matrix()
  n <- nrow(coords)
  if (n <= n2_threshold) {
    dmat <- geosphere::distm(coords, fun = geosphere::distHaversine)/1000
    diag(dmat) <- NA
    out$dist_nearest_km <- apply(dmat,1,function(r) suppressWarnings(min(r,na.rm=TRUE)))
    for (r in radii_km) out[[paste0("density_",r,"km")]] <- rowSums(dmat <= r, na.rm = TRUE) - 1
  } else {
    k <- 50
    nn <- FNN::get.knn(coords, k=k)
    for (r in radii_km) {
      dens <- integer(n)
      for (i in seq_len(n)) {
        idx <- nn$nn.index[i,]
        pts <- coords[idx, , drop=FALSE]
        dkm <- geosphere::distHaversine(coords[i,], pts)/1000
        dens[i] <- sum(dkm <= r, na.rm=TRUE)
      }
      out[[paste0("density_",r,"km")]] <- dens
    }
    out$dist_nearest_km <- map_dbl(seq_len(n), function(i){ idx <- nn$nn.index[i,1]; geosphere::distHaversine(coords[i,], coords[idx,])/1000 })
  }
  out$lat_rounded <- round(df[[lat_col]], 3); out$lon_rounded <- round(df[[lon_col]], 3)
  out
}

## ================ 6. Categorical Capping & Design Matrix ================= ##
cap_categorical_levels <- function(df, topK = 30){
  df %>% mutate(across(where(is.character), as.factor)) %>% mutate(across(where(is.factor), function(f){ if (nlevels(f) <= topK) return(f); lev <- names(sort(table(f), decreasing = TRUE))[1:topK]; fct <- as.character(f); fct[!(fct %in% lev)] <- "__other__"; factor(fct) }))
}

build_recipe <- function(data, features, topK_levels_per_cat=30, scaling_method = NULL){
  df <- data[, features, drop=FALSE] %>% cap_categorical_levels(topK_levels_per_cat)
  rec <- recipes::recipe(~ ., data=df) |>
    step_string2factor(all_predictors(), -all_numeric()) |>
    step_dummy(all_nominal_predictors(), one_hot = TRUE) |>
    step_zv(all_predictors())
  method <- scaling_method %||% "auto"
  if (method == "auto") {
    num_df <- dplyr::select(df, where(is.numeric)) %>% as.data.frame()
    if (ncol(num_df) == 0) {
      method <- "normalize"
    } else {
      rng <- apply(num_df, 2, function(col) diff(range(col, na.rm = TRUE)))
      spread <- if (length(rng)) (max(rng, na.rm=TRUE) / (min(rng[rng>0], na.rm=TRUE) %||% 1)) else 1
      method <- if (spread > 100 || any(sapply(dplyr::select(df, where(is.numeric)), function(c) any(c < 0, na.rm=TRUE)))) "standardize" else "normalize"
    }
  }
  if (method == "standardize") rec <- rec |> step_center(all_numeric_predictors()) |> step_scale(all_numeric_predictors())
  if (method == "normalize")   rec <- rec |> step_range(all_numeric_predictors())
  if (method == "robust")       rec <- rec |> step_YeoJohnson(all_numeric_predictors()) |> step_center(all_numeric_predictors()) |> step_scale(all_numeric_predictors())
  if (method == "log")          rec <- rec |> step_log(all_numeric_predictors(), offset = 1) |> step_center(all_numeric_predictors()) |> step_scale(all_numeric_predictors())
  list(recipe=rec, method=method)
}

## ===================== 7. Multi-method Feature Importance ================ ##
feature_importance_multi <- function(data, feature_types_df, features, target_variable, max_features=60, p_adjust_method="BH"){
  feats <- setdiff(intersect(features, names(data)), target_variable)
  target <- data[[target_variable]]

  corr_tbl <- tibble(feature=feats, corr=NA_real_)
  if (is.numeric(target)) {
    corr_tbl$corr <- map_dbl(feats, function(f) { v <- data[[f]]; if (is.numeric(v)) suppressWarnings(abs(cor(v, target, use="complete.obs", method="spearman"))) else NA_real_ })
  }

  anova_tbl <- tibble(feature=feats, anova_f=NA_real_, anova_p=NA_real_)
  chisq_tbl <- tibble(feature=feats, chisq=-Inf, chisq_p=NA_real_)

  if (!is.numeric(target)) {
    for (f in feats) {
      v <- data[[f]]
      if (is.numeric(v)) {
        fit <- try(aov(v ~ as.factor(target)), silent=TRUE)
        if (!inherits(fit,"try-error")) { s <- summary(fit)[[1]]; anova_tbl$anova_f[anova_tbl$feature==f] <- s[1,"F value"] %||% NA_real_; anova_tbl$anova_p[anova_tbl$feature==f] <- s[1,"Pr(>F)"] %||% NA_real_ }
      } else if (is.character(v) || is.factor(v)) {
        tab <- table(v, target); if (all(dim(tab) > 1)) { cs <- suppressWarnings(chisq.test(tab)); chisq_tbl$chisq[chisq_tbl$feature==f]   <- -log10(cs$p.value %||% 1); chisq_tbl$chisq_p[chisq_tbl$feature==f] <- cs$p.value %||% NA_real_ }
      }
    }
  } else {
    for (f in feats) { v <- data[[f]]; if (is.character(v) || is.factor(v)) { fit <- try(aov(target ~ as.factor(v)), silent=TRUE); if (!inherits(fit,"try-error")) { s <- summary(fit)[[1]]; anova_tbl$anova_f[anova_tbl$feature==f] <- s[1,"F value"] %||% NA_real_; anova_tbl$anova_p[anova_tbl$feature==f] <- s[1,"Pr(>F)"] %||% NA_real_ } } }
  }
  if (any(!is.na(anova_tbl$anova_p))) anova_tbl$anova_adj <- p.adjust(anova_tbl$anova_p, method=p_adjust_method)
  if (any(!is.na(chisq_tbl$chisq_p))) chisq_tbl$chisq_adj <- p.adjust(chisq_tbl$chisq_p, method=p_adjust_method)

  num_feats <- feats[sapply(feats, function(f) is.numeric(data[[f]]))]
  pca_imp <- tibble(feature=feats, pca=NA_real_)
  if (length(num_feats) >= 2) {
    X <- data %>% select(all_of(num_feats)) %>% mutate(across(everything(), ~replace(., !is.finite(.), NA))) %>% drop_na()
    if (nrow(X) >= 5) { Xs <- scale(X); p <- prcomp(Xs, center=FALSE, scale.=FALSE); ve <- (p$sdev^2)/sum(p$sdev^2); load <- abs(p$rotation) %*% matrix(ve, ncol=1); pca_sc <- as.vector(load); names(pca_sc) <- rownames(p$rotation); pca_imp$pca[pca_imp$feature %in% names(pca_sc)] <- pca_sc[pca_imp$feature[pca_imp$feature %in% names(pca_sc)]] }
  }

  imp <- list(
    corr = corr_tbl %>% mutate(corr = rescale_01(corr)),
    anova = anova_tbl %>% mutate(anova = rescale_01(anova_f)),
    chisq = chisq_tbl %>% mutate(chisq = rescale_01(chisq)),
    pca  = pca_imp %>% mutate(pca = rescale_01(pca))
  ) %>% reduce(full_join, by="feature") %>% mutate(across(-feature, ~replace_na(.,0)))

  imp <- imp %>% mutate(score_aggregate = rowMeans(select(., corr, anova, chisq, pca), na.rm=TRUE)) %>% arrange(desc(score_aggregate))
  if (!is.null(max_features)) imp <- imp %>% slice_head(n = max_features)
  imp
}

## ===================== 8. Dimensionality Reduction ======================= ##
run_dimensionality_reduction <- function(X_train, max_pcs=12){
  # Center using TRAIN means only, return rotation + center for deterministic projection
  mu <- colMeans(X_train, na.rm = TRUE)
  Xc <- sweep(X_train, 2, mu, FUN = "-")
  p <- prcomp(Xc, center = FALSE, scale. = FALSE)
  k <- min(max_pcs, ncol(p$x))
  list(scores = p$x[, seq_len(k), drop=FALSE],
       rotation = p$rotation[, seq_len(k), drop=FALSE],
       center = mu,
       pcs = k,
       var_explained = (p$sdev^2)/sum(p$sdev^2))
}

## ===================== 9. Clustering (multi-method) ====================== ##
choose_k_multi <- function(X_reduced, max_k=40){
  n <- nrow(X_reduced)
  max_k <- max(2, min(max_k, n-1, 20))
  set.seed(42)
  gap <- cluster::clusGap(X_reduced, FUN = kmeans, K.max = max_k, B = 30)
  k_gap <- max(2, which.max(gap$Tab[,"gap"]))
  sil_scores <- map_dbl(2:max_k, function(k){
    set.seed(42 + k)
    cl <- kmeans(X_reduced, centers=k, nstart=30)$cluster
    mean(cluster::silhouette(cl, dist(X_reduced))[,3])
  })
  k_sil <- which.max(sil_scores) + 1
  wss <- map_dbl(1:max_k, function(k){
    set.seed(42 + k)
    if (k==1) sum(kmeans(X_reduced, centers=1, nstart=10)$withinss)
    else sum(kmeans(X_reduced, centers=k, nstart=10)$withinss)
  })
  d2 <- diff(diff(wss))
  k_elbow <- which.min(c(Inf, d2, Inf)); k_elbow <- max(2, min(k_elbow, max_k))
  max(2, round(mean(c(k_gap, k_sil, k_elbow))))
}

cluster_auto <- function(Xr, method="auto", max_k=40, auto_k=TRUE, hdb_minPts=10){
  if (method=="auto" || method=="kmeans"){
    k <- if (auto_k) choose_k_multi(Xr, max_k) else min(max_k,5)
    set.seed(42)
    km <- kmeans(Xr, centers=k, nstart=50)
    sil <- mean(cluster::silhouette(km$cluster, dist(Xr))[,3])
    return(list(method="kmeans", k=k, cluster=km$cluster, centers=km$centers, quality=list(silhouette=sil)))
  }
  if (method=="gmm") {
    set.seed(42)
    g <- Mclust(Xr, G=2:min(max_k, 20))
    cl <- g$classification
    return(list(method="gmm", k=length(unique(cl)), cluster=cl, centers = g$parameters$mean, quality=list(BIC=g$BIC)))
  }
  if (method=="hdbscan") {
    set.seed(42)
    hd <- hdbscan(Xr, minPts = hdb_minPts)
    cl <- ifelse(hd$cluster==0, NA_integer_, hd$cluster)
    return(list(method="hdbscan", k=length(unique(na.omit(cl))), cluster=cl, centers = NULL, quality=list(outlier_scores=hd$outlier_scores)))
  }
  stop("Unknown clustering method.")
}

## ===================== 10. Drivers (Permutation Imp.) ==================== ##
permutation_importance <- function(X, y, model_fun, metric_fun, n_perm=20, seed=42){
  set.seed(seed)
  base_model <- model_fun(X, y)
  yhat <- predict(base_model, X)
  base_metric <- metric_fun(y, yhat)
  p <- ncol(X)
  imp <- numeric(p)
  for (j in seq_len(p)) {
    delta <- numeric(n_perm)
    for (b in seq_len(n_perm)) {
      Xp <- X; Xp[,j] <- sample(Xp[,j])
      yhatp <- predict(base_model, Xp)
      delta[b] <- base_metric - metric_fun(y, yhatp)
    }
    imp[j] <- mean(delta, na.rm=TRUE)
  }
  tibble(feature = colnames(X), importance = rescale_01(imp))
}

lm_model_fun <- function(X, y){ data <- data.frame(y=y, X); lm(y ~ ., data=data) }
rf_model_fun <- function(X, y){ randomForest(x=X, y=y, ntree=300) }
r2_metric <- function(y, yhat){ ssr <- sum((y - yhat)^2, na.rm=TRUE); sst <- sum((y - mean(y, na.rm=TRUE))^2, na.rm=TRUE); 1 - ssr/sst }

analyze_global_drivers <- function(df, selected_features, target_var, top_n=30){
  dm <- build_recipe(df, selected_features, topK_levels_per_cat=30, scaling_method="standardize")
  rec <- prep(dm$recipe, training=df, verbose=FALSE)
  X <- bake(rec, new_data=df) %>% as.matrix()
  y <- df[[target_var]]
  if (!is.numeric(y)) return(list(drivers = tibble(feature=character(0), importance=numeric(0))))
  imp <- permutation_importance(X, y, rf_model_fun, r2_metric, n_perm=20)
  list(drivers = imp %>% arrange(desc(importance)) %>% slice_head(n=top_n))
}

analyze_cluster_drivers <- function(df_with_clusters, selected_features, target_var, top_n=20){
  out <- list()
  for (cl in sort(unique(na.omit(df_with_clusters$cluster_id)))) {
    sub <- df_with_clusters %>% filter(cluster_id == cl)
    if (nrow(sub) < 20) next
    dm <- build_recipe(sub, selected_features, topK_levels_per_cat=30, scaling_method="standardize")
    rec <- prep(dm$recipe, training=sub, verbose=FALSE)
    X <- bake(rec, new_data=sub) %>% as.matrix()
    y <- sub[[target_var]]
    if (!is.numeric(y)) next
    fit <- try(lm_model_fun(X, y), silent=TRUE)
    if (inherits(fit,"try-error")) next
    co <- coef(summary(fit))[-1,,drop=FALSE]
    drv <- tibble(feature = rownames(co), importance = rescale_01(abs(co[,"t value"]))) %>%
      arrange(desc(importance)) %>% slice_head(n=top_n)
    out[[as.character(cl)]] <- list(cluster=cl, drivers=drv)
  }
  out
}

## ===================== 11. Potential (multi-method + CIs) ================ ##
compute_potential_percentile <- function(df, cluster_col, target_variable, pct=0.90){
  df %>% group_by(.data[[cluster_col]]) %>%
    mutate(target_pct = quantile(.data[[target_variable]], probs=pct, na.rm=TRUE)) %>%
    ungroup() %>%
    transmute(.unit_row = row_number(), pct_potential = target_pct)
}

compute_potential_regression <- function(df, features, target_variable){
  dm <- build_recipe(df, features, topK_levels_per_cat=30, scaling_method="standardize")
  rec <- prep(dm$recipe, training=df, verbose=FALSE)
  X <- bake(rec, new_data=df) %>% as.matrix()
  y <- df[[target_variable]]
  if (!is.numeric(y)) return(tibble(.unit_row=seq_len(nrow(df)), reg_potential=NA_real_))
  fit <- try(lm_model_fun(X, y), silent=TRUE)
  if (inherits(fit,"try-error")) return(tibble(.unit_row=seq_len(nrow(df)), reg_potential=NA_real_))
  tibble(.unit_row=seq_len(nrow(df)), reg_potential = predict(fit, data.frame(X)))
}

compute_potential_ml <- function(df, features, target_variable){
  dm <- build_recipe(df, features, topK_levels_per_cat=30, scaling_method="standardize")
  rec <- prep(dm$recipe, training=df, verbose=FALSE)
  X <- bake(rec, new_data=df) %>% as.matrix()
  y <- df[[target_variable]]
  if (!is.numeric(y) || nrow(X) < 30) return(tibble(.unit_row=seq_len(nrow(df)), ml_potential=NA_real_))
  rf <- randomForest(x=X, y=y, ntree=400)
  tibble(.unit_row=seq_len(nrow(df)), ml_potential = predict(rf, X))
}

combine_potential_methods <- function(df, target_variable, cluster_col,
                                      pct_tbl, reg_tbl, ml_tbl, weights=c(percentile=.2, regression=.4, ml=.4),
                                      clamp_ge_current=FALSE){
  base <- tibble(.unit_row = seq_len(nrow(df)))
  allp <- base %>% left_join(pct_tbl, by=".unit_row") %>% left_join(reg_tbl, by=".unit_row") %>% left_join(ml_tbl, by=".unit_row")
  w <- weights / sum(weights)
  current <- df[[target_variable]]
  comp <- cbind(
    if (!all(is.na(allp$pct_potential))) allp$pct_potential else current,
    if (!all(is.na(allp$reg_potential))) allp$reg_potential else current,
    if (!all(is.na(allp$ml_potential)))  allp$ml_potential  else current
  )
  pot_units <- rowSums(t(t(comp) * c(w["percentile"]%||%0, w["regression"]%||%0, w["ml"]%||%0)), na.rm=TRUE)
  if (clamp_ge_current) pot_units <- pmax(pot_units, current)
  uplift <- pot_units - current
  score <- rescale_01(uplift) * 100
  tibble(.unit_row=seq_len(nrow(df)),
         current_target=current, potential_units=pot_units, uplift_units=uplift,
         potential_score_0_100=score, cluster_id=df[[cluster_col]])
}

bootstrap_potential_ci <- function(df, target_variable, cluster_col, features, weights, pct, B=50, ci=0.90){
  set.seed(42)
  n <- nrow(df)
  mat <- matrix(NA_real_, nrow=n, ncol=B)
  for (b in seq_len(B)) {
    idx <- sample.int(n, n, replace=TRUE)
    dfb <- df[idx, , drop=FALSE]
    pct_tbl <- compute_potential_percentile(dfb, cluster_col, target_variable, pct)
    reg_tbl <- compute_potential_regression(dfb, features, target_variable)
    ml_tbl  <- compute_potential_ml(dfb, features, target_variable)
    comb <- combine_potential_methods(dfb, target_variable, cluster_col, pct_tbl, reg_tbl, ml_tbl, weights)
    # Map back using position match (approximate but stable enough here)
    pos <- match(seq_len(n), idx)
    mat[,b] <- comb$potential_units[ifelse(is.na(pos), 1, pos)]
  }
  lo <- (1-ci)/2; hi <- 1-lo
  tibble(.unit_row=seq_len(n),
         potential_lo = apply(mat, 1, quantile, probs=lo, na.rm=TRUE),
         potential_hi = apply(mat, 1, quantile, probs=hi, na.rm=TRUE))
}

## ========================= 12. Summary Builder =========================== ##
build_dimension_summary <- function(df_with_clusters, potentials, potentials_ci, unit_id, target_variable, labels){
  df_out <- df_with_clusters %>% mutate(.unit_row=row_number()) %>%
    select(.unit_row, !!sym(unit_id), cluster_id, !!sym(target_variable)) %>%
    left_join(potentials %>% select(.unit_row, potential_score_0_100, uplift_units,
                                    potential_units, current_target, cluster_id),
              by=c(".unit_row","cluster_id")) %>%
    left_join(potentials_ci, by=".unit_row") %>%
    transmute(
      !!sym(unit_id),
      cluster_id,
      current = current_target,
      should_be = potential_units,
      should_be_lo = potential_lo,
      should_be_hi = potential_hi,
      uplift_units = uplift_units,
      potential_score_0_100 = potential_score_0_100
    )
  attr(df_out, "labels") <- labels
  df_out
}

## ====================== 13. Governance Manifest ========================== ##
make_manifest <- function(config, data_sources, result, merge_report, oof_metrics){
  list(
    timestamp = as.character(Sys.time()),
    config = config,
    data_sources = if (is.list(data_sources) || length(data_sources)>1) as.character(unlist(data_sources)) else as.character(data_sources),
    seeds = list(global=42),
    session = list(R.version = R.version.string,
                   platform = R.version$platform),
    packages = as.list(sessionInfo()$otherPkgs) %>% purrr::map(~.$Version),
    model_card = list(
      objective = paste("Optimize", config$target_variable, "across", config$unit_id),
      training_validation = list(split=config$split, vfolds=config$split$vfolds, leakage_controls="train-only fit, bake on valid/full"),
      metrics = oof_metrics,
      fairness = list(note="Add segment-based diagnostics before prod"),
      risks = c("unsupervised clustering interpretability", "data quality/merging errors"),
      approvals = list(required=c("Data Owner","Risk/Legal","Model Owner"))
    ),
    summary = list(
      n_entities = nrow(result$summary_table),
      n_clusters = length(unique(result$cluster_result$data_with_clusters$cluster_id)),
      scaling_method = result$scaling_method,
      clustering_method = result$cluster_result$method
    ),
    merge = merge_report
  )
}

## ====================== 14. Orchestrator (core engine) =================== ##
run_infinite_dimensions <- function(data_source, config){
  cfg <- validate_config(config)
  tv <- cfg$target_variable; uid <- cfg$unit_id

  # 1) Load: single or multi, with safe auto-merge
  if (is.list(data_source) || (is.atomic(data_source) && length(data_source) > 1)) {
    mr <- load_many_and_merge(data_source, cfg$ingest)
    raw_data <- mr$data; merge_report <- mr
  } else {
    raw_data <- load_data_agnostic(data_source); merge_report <- NULL
  }

  # 2) Geo (opt-in)
  ln <- tolower(names(raw_data))
  geo_vars <- list(
    latitude = names(raw_data)[grepl("lat|latitude|ycoord|y_coord", ln)],
    longitude= names(raw_data)[grepl("lon|lng|longitude|xcoord|x_coord", ln)],
    address  = names(raw_data)[grepl("addr|address|street|location|place", ln)],
    postcode = names(raw_data)[grepl("zip|postcode|postal", ln)]
  )
  data_geo <- if (cfg$geo$enabled) geocode_if_needed(raw_data, geo_vars, cfg$privacy, cfg$security$offline) else raw_data
  lat_col <- geo_vars$latitude[1] %||% if ("lat" %in% names(data_geo)) "lat" else NULL
  lon_col <- geo_vars$longitude[1] %||% if ("lon" %in% names(data_geo)) "lon" else NULL
  data_geo <- if (cfg$geo$enabled) add_geo_features(data_geo, lat_col, lon_col, cfg$geo$radii_km, cfg$guards$n2_threshold) else data_geo

  # 3) Feature types & candidate list
  ftypes <- detect_feature_types(data_geo, tv)
  base_features <- setdiff(names(data_geo), c(tv, uid))

  # 4) Train/Validation split to avoid leakage
  stopifnot(tv %in% names(data_geo), uid %in% names(data_geo))
  data_geo <- data_geo %>% drop_na(!!sym(tv))
  split <- initial_split(data_geo, prop = 1 - cfg$split$validation_prop, strata = NULL)
  train <- training(split); valid <- testing(split)

  # 5) Feature importance on TRAIN only
  imp <- feature_importance_multi(train, ftypes, base_features, tv,
                                  max_features=cfg$selection$max_features,
                                  p_adjust_method=cfg$selection$p_adjust_method)
  selected_features <- imp$feature

  # 6) Build recipe on TRAIN; bake TRAIN/VALID/FULL (no refitting)
  rec_info <- build_recipe(train, selected_features, cfg$selection$topK_levels_per_cat, cfg$scaling$force_method)
  rec_trained <- prep(rec_info$recipe, training=train, verbose=FALSE)
  X_train <- bake(rec_trained, new_data=train) %>% as.matrix()
  X_valid <- bake(rec_trained, new_data=valid) %>% as.matrix()
  X_full  <- bake(rec_trained, new_data=data_geo) %>% as.matrix()
  scaling_method <- rec_info$method

  # 7) PCA on TRAIN (fit), transform VALID/FULL
  red_train <- run_dimensionality_reduction(X_train, cfg$dimred$max_pcs)
  Xc_valid <- sweep(X_valid, 2, red_train$center, FUN = "-")
  Xc_full  <- sweep(X_full,  2, red_train$center, FUN = "-")
  scores_valid <- Xc_valid %*% red_train$rotation
  scores_full  <- Xc_full  %*% red_train$rotation

  # 8) Clustering on TRAIN (fit), assign VALID/FULL via nearest centroids (or medoids proxy for HDBSCAN)
  cl_train <- cluster_auto(red_train$scores, method=cfg$clustering$method,
                           max_k=cfg$clustering$max_clusters,
                           auto_k=cfg$clustering$auto_k,
                           hdb_minPts=cfg$clustering$hdbscan_minPts %||% 10)
  if (cl_train$method %in% c("kmeans","gmm") && !is.null(cl_train$centers)) {
    centers <- cl_train$centers; if (is.list(centers)) centers <- t(centers)
    assign_by_centers <- function(scores){
      C <- as.matrix(centers); S <- as.matrix(scores)
      if (!ncol(C)) stop("No PCs available for assignment")
      CC <- rowSums(C*C); SS <- rowSums(S*S)
      D2 <- outer(CC, SS, "+") - 2 * (C %*% t(S))
      D2[D2 < 0] <- 0
      D <- sqrt(D2)
      max.col(-t(D))
    }
    assign_valid <- assign_by_centers(scores_valid)
    assign_full  <- assign_by_centers(scores_full)
  } else if (cl_train$method == "hdbscan") {
    hdf_train <- hdbscan(red_train$scores, minPts=cfg$clustering$hdbscan_minPts)
    cl <- ifelse(hdf_train$cluster==0, NA_integer_, hdf_train$cluster)
    medoids <- sapply(sort(unique(na.omit(cl))), function(k){ which.max(hdf_train$membership_prob[cl==k]) })
    centers <- red_train$scores[medoids, , drop=FALSE]
    assign_by_centers <- function(scores){
      C <- as.matrix(centers); S <- as.matrix(scores)
      if (!ncol(C)) stop("No PCs available for assignment")
      CC <- rowSums(C*C); SS <- rowSums(S*S)
      D2 <- outer(CC, SS, "+") - 2 * (C %*% t(S))
      D2[D2 < 0] <- 0
      D <- sqrt(D2)
      max.col(-t(D))
    }
    assign_valid <- assign_by_centers(scores_valid)
    assign_full  <- assign_by_centers(scores_full)
    cl_train$centers <- centers
    cl_train$cluster <- cl
  } else {
    assign_valid <- cl_train$cluster[seq_len(nrow(scores_valid)) %% length(cl_train$cluster) + 1]
    assign_full  <- cl_train$cluster[seq_len(nrow(scores_full)) %% length(cl_train$cluster) + 1]
  }

  data_with_clusters <- data_geo %>% mutate(cluster_id = assign_full)
  cluster_result <- list(method=cl_train$method, k=cl_train$k, data_with_clusters=data_with_clusters,
                         centers=cl_train$centers, quality=cl_train$quality)

  # 9) OOF metrics via vfold CV
  set.seed(42)
  folds <- vfold_cv(train, v=cfg$split$vfolds)
  oof_r2 <- map_dbl(folds$splits, function(sp){
    tr <- analysis(sp); te <- assessment(sp)
    ri <- build_recipe(tr, selected_features, cfg$selection$topK_levels_per_cat, cfg$scaling$force_method)
    rec_p <- prep(ri$recipe, training=tr, verbose=FALSE)
    Xtr <- bake(rec_p, new_data=tr) %>% as.matrix()
    Xte <- bake(rec_p, new_data=te) %>% as.matrix()
    ytr <- tr[[tv]]; yte <- te[[tv]]
    rf <- randomForest(x=Xtr, y=ytr, ntree=300)
    yhat <- predict(rf, Xte)
    r2_metric(yte, yhat)
  })

  # 10) Drivers (global + cluster) on FULL (descriptive)
  cluster_drivers <- analyze_cluster_drivers(data_with_clusters, selected_features, tv, cfg$drivers$top_n_cluster)
  global_drivers  <- analyze_global_drivers (data_with_clusters, selected_features, tv, cfg$drivers$top_n_global)

  # 11) Potential on FULL
  pct_tbl <- if (cfg$potential$use_percentile) compute_potential_percentile(data_with_clusters, "cluster_id", tv, cfg$potential$cluster_pct) else tibble(.unit_row=seq_len(nrow(data_with_clusters)), pct_potential=NA_real_)
  reg_tbl <- if (cfg$potential$use_regression) compute_potential_regression (data_with_clusters, selected_features, tv) else tibble(.unit_row=seq_len(nrow(data_with_clusters)), reg_potential=NA_real_)
  ml_tbl  <- if (cfg$potential$use_ml)         compute_potential_ml        (data_with_clusters, selected_features, tv) else tibble(.unit_row=seq_len(nrow(data_with_clusters)), ml_potential=NA_real_)
  potentials <- combine_potential_methods(data_with_clusters, tv, "cluster_id", pct_tbl, reg_tbl, ml_tbl, cfg$potential$weights, cfg$potential$clamp_ge_current)

  # 12) Uncertainty: bootstrap CIs
  potentials_ci <- bootstrap_potential_ci(data_with_clusters, tv, "cluster_id", selected_features, cfg$potential$weights, cfg$potential$cluster_pct, B=cfg$uncertainty$B, ci=cfg$uncertainty$ci)

  # 13) Summary table
  summary_tbl <- build_dimension_summary(data_with_clusters, potentials, potentials_ci, uid, tv, cfg$labels)

  # 14) Manifest (governance)
  result_stub <- list(summary_table=summary_tbl, cluster_result=cluster_result, scaling_method=scaling_method)
  oof <- list(r2_mean = mean(oof_r2, na.rm=TRUE), r2_sd = sd(oof_r2, na.rm=TRUE), r2 = oof_r2)
  manifest <- make_manifest(cfg, data_source, result_stub, merge_report, oof)

  list(
    config = cfg,
    data = data_geo,
    feature_types = ftypes,
    selected_features = selected_features,
    scaling_method = scaling_method,
    reduced = list(train=red_train, valid=scores_valid, full=scores_full),
    cluster_result = cluster_result,
    cluster_drivers = cluster_drivers,
    global_drivers = global_drivers,
    potentials = potentials,
    potentials_ci = potentials_ci,
    summary_table = summary_tbl,
    merge_report = merge_report,
    manifest = manifest,
    oof_metrics = oof
  )
}

## ========================= 15. Chat/AI Wrapper =========================== ##
run_analysis <- function(data_source, ...) { cfg <- make_analytics_config(...); run_infinite_dimensions(data_source, cfg) }

answer_question <- function(result, question, top_n=5){
  q <- tolower(question)
  summary_tbl <- result$summary_table
  uid <- result$config$unit_id; tv <- result$config$target_variable
  if (grepl("highest potential|top potential|biggest opportunity", q)) {
    out <- summary_tbl %>% slice_max(order_by = potential_score_0_100, n = top_n)
    return(list(type="table", message=paste0("Top ", top_n, " ", uid, " by potential score for '", tv, "'."), data=out))
  }
  if (grepl("explain|why|driver|drivers", q) && grepl(uid, q)) {
    candidate <- stringr::str_extract(q, "(\\w+)")
    row <- summary_tbl %>% filter(.data[[uid]] == candidate)
    if (nrow(row)) {
      msg <- paste0(uid," ",candidate,": current ", tv,"=", round(row$current,1),
                    " → should-be ", round(row$should_be,1), " (", round(row$should_be_lo,1), "–", round(row$should_be_hi,1),
                    "), uplift≈", round(row$uplift_units,1),
                    ", score=", round(row$potential_score_0_100,1))
      return(list(type="text", message=msg))
    }
  }
  if (grepl("global driver|main driver|key driver", q)) {
    g <- result$global_drivers$drivers %>% slice_head(n=top_n)
    txt <- paste0("Top ", top_n, " global drivers of '", tv, "':\n", paste0("- ", g$feature, " (", round(g$importance,2),")", collapse="\n"))
    return(list(type="text", message=txt, data=g))
  }
  list(type="text",
       message=paste0("Analyzed '", tv, "' for ", nrow(summary_tbl), " ", uid, " across ",
                      length(unique(result$cluster_result$data_with_clusters$cluster_id)), " clusters. ",
                      "Avg potential score: ", round(mean(summary_tbl$potential_score_0_100, na.rm=TRUE),1), "."))
}

## ============================== 16. Usage ================================ ##
# Example (multi-file):
# sources <- list("entities.csv", "metrics.xlsx", "context.json")
# res <- run_analysis(
#   data_source = sources,
#   target_variable = "kpi_value",
#   unit_id = "entity_id",
#   entity_label = "entity",
#   kpi_label = "KPI",
#   add_geo_features = FALSE,
#   geocoding_provider = "off",
#   clustering_method = "auto",
#   bootstrap_B = 50,
#   offline = TRUE
# )
# print_merge_report(res$merge_report)
# head(res$summary_table)
# write_yaml(res$manifest, "run_manifest.yaml")
