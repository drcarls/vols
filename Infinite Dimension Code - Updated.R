





# Here you go — a single, coherent R script that stitches the whole pipeline together 
# (ingest → geo → feature engineering & selection → scaling → dimensionality reduction → 
# multi-method K selection → clustering → drivers → multi-method potential (score + units) 
# → summary table) plus a thin “AI wrapper” (run_analysis, answer_question) and a few ready-to-use templates.



# ---- Neutral labels (drop-in) ---- Make this neutral (bench mark anything)
label_config <- function(
    entity_label  = "entity",      # e.g., "customer", "agent", "SKU", "machine", "campaign", "widgets"
    plural_label  = NULL,          # if NULL -> entity_label + "s"
    kpi_label     = "KPI",         # e.g., "revenue", "uptime", "AUC", "CTR"
    score_label   = "Potential score (0–100)"
) {
  list(
    entity_label = entity_label,
    plural_label = plural_label %||% paste0(entity_label, "s"),
    kpi_label    = kpi)}






###############################################################################
# Infinite Dimensions Performance Engine — Single-File Implementation
# (ingest → geo → feature selection → scaling → PCA → clustering → drivers →
#  multi-method potential → summary table) + Chat-style wrapper
###############################################################################

## ============================== 0. Libraries ============================== ##
suppressPackageStartupMessages({
  library(tidyverse)
  library(readxl)
  library(jsonlite)
  library(httr)
  library(geosphere)     # distHaversine
  library(cluster)       # silhouette, clusGap
  library(furrr)         # parallel mapping (optional)
  library(recipes)       # dummy vars
  library(randomForest)  # ML potential
})


    
    
plan(multisession, workers = max(1, parallel::detectCores() - 1))



############# merge multiple data files together #################
# Optional but helpful: install.packages("janitor")
suppressPackageStartupMessages({ library(janitor) })

make_clean <- function(df) {
  df %>% janitor::clean_names() %>% as_tibble()
}

uniqueness_ratio <- function(x) {
  x2 <- x[!is.na(x)]
  if (length(x2) == 0) return(0)
  length(unique(x2)) / length(x2)
}

value_overlap_score <- function(a, b) {
  a2 <- unique(na.omit(a)); b2 <- unique(na.omit(b))
  if (length(a2) == 0 || length(b2) == 0) return(0)
  inter <- length(intersect(a2, b2))
  union <- length(unique(c(a2, b2)))
  inter / union
}

# Heuristic: columns that look like IDs or good keys
score_key_column <- function(df, col) {
  v <- df[[col]]
  base <- uniqueness_ratio(v)
  name_bonus <- ifelse(grepl("(?:^|_)(id|code|uuid|sku|email)$", col), 0.2, 0)
  type_bonus <- ifelse(is.numeric(v) || is.character(v), 0.05, 0)
  pmin(1, base + name_bonus + type_bonus)
}

# Try small composite keys if singles aren't great
best_composite_keys <- function(df, max_size = 2, top_k = 6) {
  cands <- names(df)
  # keep plausible columns
  cands <- cands[sapply(cands, function(nm) {
    v <- df[[nm]]
    is.numeric(v) || is.character(v) || is.factor(v)
  })]
  # score singles
  singles <- tibble(
    cols = map(cands, ~.x),
    score = map_dbl(cands, ~score_key_column(df, .x))
  ) %>% arrange(desc(score)) %>% slice_head(n = top_k)
  
  # try pairs
  pairs <- combn(singles$cols, 2, simplify = FALSE)
  pair_scores <- map_dbl(pairs, function(p) {
    key <- df %>% unite("__key__", all_of(p), sep = "||", remove = FALSE, na.rm = TRUE) %>% pull("__key__")
    uniqueness_ratio(key)
  })
  if (length(pair_scores) == 0) {
    return(singles %>% mutate(type = "single"))
  }
  pair_tbl <- tibble(cols = pairs, score = pair_scores) %>% mutate(type = "pair")
  bind_rows(singles %>% mutate(type = "single"), pair_tbl) %>% arrange(desc(score))
}


load_many_and_merge <- function(data_sources,
                                prefer_keys = c("id", "store_id", "customer_id", "campaign_id"),
                                min_overlap = 0.2,
                                min_key_quality = 0.6,
                                verbose = TRUE) {
  # 1) Load & clean each source
  dfs <- map(data_sources, function(src) make_clean(load_data_agnostic(src)))
  names(dfs) <- names(dfs) %||% paste0("df", seq_along(dfs))

  # 2) Detect candidate keys in each df
  key_candidates <- map(dfs, ~best_composite_keys(.x))
  # 3) If any preferred key exists exactly, bump it
  key_candidates <- imap(key_candidates, function(tbl, nm) {
    if (any(prefer_keys %in% names(dfs[[nm]]))) {
      pk <- prefer_keys[prefer_keys %in% names(dfs[[nm]])][1]
      tibble(cols = list(pk), score = 1, type = "preferred") %>% bind_rows(tbl)
    } else tbl
  })

  # 4) Pick a base (largest rows, good key)
  sizes <- map_int(dfs, nrow)
  order_base <- order(sizes, decreasing = TRUE)
  base_name <- NULL; base_key <- NULL

  for (nm in names(dfs)[order_base]) {
    kc <- key_candidates[[nm]] %>% slice(1)
    if (nrow(kc) && kc$score[1] >= min_key_quality) { base_name <- nm; base_key <- kc$cols[[1]]; break }
  }
  if (is.null(base_name)) { base_name <- names(dfs)[order_base][1]; base_key <- key_candidates[[base_name]]$cols[[1]] }

  base_df <- dfs[[base_name]]
  if (length(base_key) > 1) base_df <- base_df %>% unite(".__merge_key__", all_of(base_key), sep="||", remove=FALSE, na.rm=TRUE)
  else names(base_df)[names(base_df) == base_key] <- ".__merge_key__"

  # 5) Iteratively merge other dfs onto base
  merge_steps <- list()
  used <- base_name
  merged <- base_df

  for (nm in setdiff(names(dfs), base_name)) {
    right <- dfs[[nm]]
    # detect best matching key between merged and right
    kc_right <- key_candidates[[nm]] %>% slice_head(n = 6)

    # ensure right has key column "__r_key__"
    chosen_right <- NULL
    for (cols in kc_right$cols) {
      tmp <- right
      if (length(cols) > 1) tmp <- tmp %>% unite("__r_key__", all_of(cols), sep="||", remove=FALSE, na.rm=TRUE)
      else names(tmp)[names(tmp) == cols] <- "__r_key__"

      ov <- value_overlap_score(merged$.__merge_key__, tmp$`__r_key__`)
      if (ov >= min_overlap) { chosen_right <- list(cols = cols, ov = ov); right <- tmp; break }
    }

    # fallback: try natural common columns (same names)
    if (is.null(chosen_right)) {
      commons <- intersect(names(merged), names(right))
      commons <- setdiff(commons, c(".__merge_key__", "__r_key__"))
      # heuristics: id-like first
      commons <- c(intersect(prefer_keys, commons), setdiff(commons, prefer_keys))
      if (length(commons)) {
        best <- NULL; best_ov <- 0
        for (c in commons) {
          ov <- value_overlap_score(merged[[c]], right[[c]])
          if (ov > best_ov) { best <- c; best_ov <- ov }
        }
        if (!is.null(best) && best_ov >= min_overlap) {
          # align both sides to __r_key__/__merge_key__
          names(right)[names(right) == best] <- "__r_key__"
          names(merged)[names(merged) == best] <- ".__merge_key__"
          chosen_right <- list(cols = best, ov = best_ov, via_common = TRUE)
        }
      }
    }

    # Perform left join from merged → right
    if (!is.null(chosen_right)) {
      keep_cols <- setdiff(names(right), "__r_key__")
      before_n <- nrow(merged)
      merged <- merged %>% left_join(right %>% rename(.__merge_key__ = `__r_key__`), by = ".__merge_key__")
      after_n <- nrow(merged)

      merge_steps[[length(merge_steps)+1]] <- list(
        right_df = nm,
        right_key = chosen_right$cols,
        overlap = chosen_right$ov,
        join_col = ".__merge_key__",
        rows_before = before_n,
        rows_after  = after_n,
        cols_added  = setdiff(keep_cols, names(base_df))
      )
      used <- c(used, nm)
    } else {
      merge_steps[[length(merge_steps)+1]] <- list(
        right_df = nm,
        right_key = NA, overlap = 0, join_col = NA,
        rows_before = nrow(merged), rows_after = nrow(merged),
        cols_added = character(0),
        note = "no suitable key found (skipped)"
      )
    }
  }

  # 6) Housekeeping: if original base key(s) existed, keep them named
  if ("__merge_key__" %in% names(merged) && !any(names(base_df) == "__merge_key__")) {
    # keep internal key, but you can drop if undesired
    # merged <- merged %>% select(-.__merge_key__)
  }

  list(
    data = merged,
    base = list(name = base_name, key = base_key),
    steps = merge_steps,
    key_candidates = key_candidates,
    used_order = used
  )
}

print_merge_report <- function(merge_result) {
  cat("=== Auto-Merge Report ===\n")
  cat("Base table:", merge_result$base$name, " | Base key:", paste(merge_result$base$key, collapse = "+"), "\n")
  for (s in merge_result$steps) {
    cat("\n→ Joined:", s$right_df, "\n")
    if (!is.null(s$note)) { cat("   ", s$note, "\n"); next }
    cat("   Right key:", paste(s$right_key, collapse = "+"), "\n")
    cat("   Overlap (Jaccard):", round(s$overlap, 3), "\n")
    cat("   Rows:", s$rows_before, "→", s$rows_after, "\n")
    cat("   New cols:", paste(s$cols_added, collapse = ", "), "\n")
  }
  cat("\nTotal columns:", ncol(merge_result$data), " | Total rows:", nrow(merge_result$data), "\n")
}


## =========================== 1. Global Utilities ========================= ##
`%||%` <- function(a, b) if (is.null(a)) b else a

rescale_01 <- function(x) {
  if (all(is.na(x))) return(x)
  rng <- range(x, na.rm = TRUE)
  if (diff(rng) == 0) return(rep(0.5, length(x)))
  (x - rng[1]) / diff(rng)
}

safe_sd <- function(x) sd(x, na.rm = TRUE)
safe_mean <- function(x) mean(x, na.rm = TRUE)
na0 <- function(x) { x[is.na(x)] <- 0; x }

## ============================== 2. Config ================================ ##
make_analytics_config <- function(
    target_variable,
    unit_id,
    # feature selection
    max_features           = 50,
    # dimensionality reduction
    max_pcs                = 10,
    # clustering
    max_clusters           = 50,
    auto_k                 = TRUE,
    # driver analysis
    top_n_cluster_drivers  = 20,
    top_n_global_drivers   = 30,
    # potential methods & weights
    use_regression         = TRUE,
    use_ml                 = TRUE,
    use_percentile         = TRUE,
    regression_weight      = 0.4,
    ml_weight              = 0.4,
    percentile_weight      = 0.2,
    cluster_percentile_target = 0.90,
    # scaling
    force_scaling_method   = NULL  # NULL = auto, or "standardize"/"normalize"/"robust"/"log_scale"/"none"
) {
  list(
    target_variable = target_variable,
    unit_id         = unit_id,
    feature = list(max_features = max_features),
    dimred  = list(max_pcs = max_pcs),
    clustering = list(max_clusters = max_clusters, auto_k = auto_k),
    drivers = list(top_n_cluster = top_n_cluster_drivers, top_n_global = top_n_global_drivers),
    potential = list(
      use_regression = use_regression,
      use_ml = use_ml,
      use_percentile = use_percentile,
      regression_weight = regression_weight,
      ml_weight = ml_weight,
      percentile_weight = percentile_weight,
      cluster_percentile_target = cluster_percentile_target
    ),
    scaling = list(force_method = force_scaling_method)
  )
}

## ====================== 3. Data Loading (schema-agnostic) ================ ##
load_data_agnostic <- function(data_source) {
  if (is.character(data_source)) {
    if (grepl("\\.csv$", data_source, ignore.case = TRUE)) {
      readr::read_csv(data_source, show_col_types = FALSE)
    } else if (grepl("\\.xlsx?$", data_source, ignore.case = TRUE)) {
      readxl::read_excel(data_source)
    } else if (grepl("\\.json$", data_source, ignore.case = TRUE)) {
      jsonlite::fromJSON(data_source, simplifyVector = TRUE) %>% as_tibble()
    } else {
      stop("Unsupported file format. Use .csv, .xlsx, or .json, or pass a data.frame/tibble.")
    }
  } else if (inherits(data_source, "data.frame") || tibble::is_tibble(data_source)) {
    as_tibble(data_source)
  } else {
    stop("Data source must be a filepath or a data.frame/tibble.")
  }
}

## ===================== 4. Feature Type Detection ========================= ##
detect_feature_types <- function(df, target_variable = NULL) {
  cols <- names(df)
  tibble(
    feature = cols,
    type = map_chr(cols, function(cn) {
      v <- df[[cn]]
      if (!is.null(target_variable) && cn == target_variable) return("target")
      if (is.numeric(v)) {
        # heuristic: low-card numeric treated numeric still (encoding happens later if needed)
        return("numeric")
      } else if (is.logical(v)) {
        return("binary")
      } else if (is.factor(v) || is.character(v)) {
        # if too many unique, still "categorical" (we'll one-hot top levels)
        return("categorical")
      } else {
        "other"
      }
    })
  )
}

## ===================== 5. Geospatial: detect + geocode ==================== ##
is_lat <- function(x) is.numeric(x) && all(x >= -90 & x <= 90, na.rm = TRUE)
is_lon <- function(x) is.numeric(x) && all(x >= -180 & x <= 180, na.rm = TRUE)

detect_geospatial_variables <- function(df) {
  nms <- names(df)
  ln <- tolower(nms)
  lat_cands <- nms[grepl("lat|latitude|ycoord|y_coord", ln)]
  lon_cands <- nms[grepl("lon|lng|longitude|xcoord|x_coord", ln)]
  addr_cands <- nms[grepl("addr|address|street|location|place", ln)]
  post_cands <- nms[grepl("zip|postcode|postal", ln)]
  lat <- lat_cands[map_lgl(lat_cands, ~ is_lat(df[[.x]]))]
  lon <- lon_cands[map_lgl(lon_cands, ~ is_lon(df[[.x]]))]
  list(latitude = lat, longitude = lon, address = addr_cands, postcode = post_cands)
}

geocode_osm_single <- function(address) {
  url <- "https://nominatim.openstreetmap.org/search"
  resp <- httr::GET(url, query = list(q = address, format = "json", limit = 1),
                    httr::add_headers(`User-Agent` = "infinite-dim-engine/1.0"))
  if (httr::status_code(resp) == 200) {
    js <- httr::content(resp, as = "parsed")
    if (length(js) > 0) {
      return(list(lat = as.numeric(js[[1]]$lat), lon = as.numeric(js[[1]]$lon)))
    }
  }
  list(lat = NA_real_, lon = NA_real_)
}

geocode_if_needed <- function(df, geo_vars, address_priority = TRUE) {
  out <- df
  has_lat <- length(geo_vars$latitude) > 0
  has_lon <- length(geo_vars$longitude) > 0
  if (has_lat && has_lon) return(out)  # already has coords
  
  # Try to geocode if we have address-like fields
  addr_col <- geo_vars$address[1] %||% geo_vars$postcode[1]
  if (address_priority && !is.null(addr_col)) {
    addrs <- df[[addr_col]] %>% as.character()
    uniq <- unique(na.omit(addrs))
    if (length(uniq) > 0) {
      message("Geocoding addresses via OSM... (rate-limited)")
      geocoded <- map_dfr(uniq, function(a) {
        Sys.sleep(1/2) # be polite to OSM
        rec <- geocode_osm_single(a)
        tibble(.__address__ = a, lat = rec$lat, lon = rec$lon)
      })
      out <- out %>% mutate(.__address__ = !!sym(addr_col)) %>%
        left_join(geocoded, by = ".__address__") %>% select(-.__address__)
      return(out)
    }
  }
  out
}

## ============= 6. Geo Feature Engineering: distances & densities ========= ##
add_geo_features <- function(df, lat_col = NULL, lon_col = NULL, radii_km = c(1, 5)) {
  out <- df
  if (!is.null(lat_col) && !is.null(lon_col) && lat_col %in% names(df) && lon_col %in% names(df)) {
    coords <- df %>% select(all_of(c(lon_col, lat_col))) %>% as.matrix()
    if (nrow(coords) >= 2 && all(is.finite(coords))) {
      # nearest neighbor distance (km)
      dmat <- geosphere::distm(coords, fun = geosphere::distHaversine) / 1000
      diag(dmat) <- NA
      out$dist_nearest_km <- apply(dmat, 1, function(r) suppressWarnings(min(r, na.rm = TRUE)))
      # density within radii
      for (r in radii_km) {
        out[[paste0("density_", r, "km")]] <- rowSums(dmat <= r, na.rm = TRUE) - 1
      }
    }
    out$lat_rounded <- round(df[[lat_col]], 3)
    out$lon_rounded <- round(df[[lon_col]], 3)
  }
  out
}

## =================== 7. Design Matrix (encode categoricals) ============== ##
build_numeric_design_matrix <- function(data, features, feature_types_df) {
  feats <- intersect(features, names(data))
  ft <- feature_types_df %>% filter(feature %in% feats)
  # recipe: one-hot for categorical, keep numerics
  rec <- recipes::recipe(~ ., data = data[, feats, drop = FALSE]) |>
    step_string2factor(all_predictors(), -all_numeric()) |>
    step_dummy(all_nominal_predictors(), one_hot = TRUE) |>
    step_zv(all_predictors())
  prepped <- prep(rec)
  X <- bake(prepped, new_data = NULL) %>% as.matrix()
  list(X = X, recipe = prepped)
}

## ==================== 8. Scaling & Dominance Handling ==================== ##
recommend_scaling_method <- function(X) {
  rng <- apply(X, 2, function(col) diff(range(col, na.rm = TRUE)))
  if (any(is.infinite(rng) | is.na(rng))) return("standardize")
  spread <- (max(rng, na.rm = TRUE) / (min(rng[rng > 0], na.rm = TRUE) %||% 1))
  # Heuristics
  if (spread > 100) return("standardize")
  if (any(apply(X, 2, function(c) any(c < 0, na.rm = TRUE)))) return("standardize")
  "normalize"
}

apply_feature_scaling <- function(X, method = c("standardize","normalize","robust","log_scale","none")[1]) {
  Z <- X
  for (j in seq_len(ncol(X))) {
    v <- X[, j]
    if (!is.numeric(v)) next
    v2 <- v
    if (method == "standardize") {
      sdv <- sd(v, na.rm = TRUE)
      m   <- mean(v, na.rm = TRUE)
      v2  <- ifelse(is.finite(sdv) && sdv > 0, (v - m)/sdv, 0)
    } else if (method == "normalize") {
      minv <- min(v, na.rm = TRUE)
      maxv <- max(v, na.rm = TRUE)
      v2 <- if (is.finite(minv) && is.finite(maxv) && maxv > minv) (v - minv)/(maxv - minv) else 0
    } else if (method == "robust") {
      med <- median(v, na.rm = TRUE); i <- IQR(v, na.rm = TRUE)
      v2 <- if (is.finite(i) && i > 0) (v - med)/i else 0
    } else if (method == "log_scale") {
      if (all(v > 0, na.rm = TRUE)) {
        lv <- log(v)
        sdv <- sd(lv, na.rm = TRUE); m <- mean(lv, na.rm = TRUE)
        v2 <- ifelse(is.finite(sdv) && sdv > 0, (lv - m)/sdv, 0)
      } else {
        v2 <- v  # fallback
      }
    } else if (method == "none") {
      v2 <- v
    }
    Z[, j] <- ifelse(is.finite(v2), v2, 0)
  }
  Z[is.na(Z)] <- 0
  Z
}

## ================== 9. Multi-method Feature Importance ================== ##
# Returns tibble(feature, score_aggregate, method_* columns)
feature_importance_multi <- function(data, feature_types_df, features, target_variable, max_features = 50) {
  feats <- setdiff(intersect(features, names(data)), target_variable)
  target <- data[[target_variable]]
  
  # A) correlation (numeric features vs numeric target)
  corr_tbl <- tibble(feature = feats, corr = NA_real_)
  if (is.numeric(target)) {
    corr_tbl$corr <- map_dbl(feats, function(f) {
      v <- data[[f]]
      if (is.numeric(v)) suppressWarnings(abs(cor(v, target, use = "complete.obs", method = "spearman"))) else NA_real_
    })
  }
  
  # B) ANOVA (numeric feature grouped by categorical target) OR (target numeric ~ factor feature)
  anova_tbl <- tibble(feature = feats, anova_f = NA_real_)
  if (!is.numeric(target)) {
    for (f in feats) {
      v <- data[[f]]
      if (is.numeric(v)) {
        fit <- try(aov(v ~ as.factor(target)), silent = TRUE)
        if (!inherits(fit, "try-error")) {
          s <- summary(fit)[[1]]
          anova_tbl$anova_f[anova_tbl$feature == f] <- s[1, "F value"] %||% NA_real_
        }
      }
    }
  } else {
    # target numeric ~ factor feature F value (via one-way)
    for (f in feats) {
      v <- data[[f]]
      if (is.character(v) || is.factor(v)) {
        fit <- try(aov(target ~ as.factor(v)), silent = TRUE)
        if (!inherits(fit, "try-error")) {
          s <- summary(fit)[[1]]
          anova_tbl$anova_f[anova_tbl$feature == f] <- s[1, "F value"] %||% NA_real_
        }
      }
    }
  }
  
  # C) Chi-squared (feature categorical vs target categorical)
  chisq_tbl <- tibble(feature = feats, chisq = NA_real_)
  if (!is.numeric(target)) {
    for (f in feats) {
      v <- data[[f]]
      if (is.character(v) || is.factor(v)) {
        tab <- table(v, target)
        if (all(dim(tab) > 1)) {
          cs <- suppressWarnings(chisq.test(tab))
          chisq_tbl$chisq[chisq_tbl$feature == f] <- -log10(cs$p.value %||% 1)
        }
      }
    }
  }
  
  # D) PCA loading-based contribution (numeric features only)
  num_feats <- feats[sapply(feats, function(f) is.numeric(data[[f]]))]
  pca_imp <- tibble(feature = feats, pca = NA_real_)
  if (length(num_feats) >= 2) {
    X <- data %>% select(all_of(num_feats)) %>% mutate(across(everything(), ~replace(., !is.finite(.), NA))) %>% drop_na()
    if (nrow(X) >= 5) {
      Xs <- scale(X)
      pca <- prcomp(Xs, center = FALSE, scale. = FALSE)
      # contribution score: sum of absolute loadings weighted by variance explained
      ve <- (pca$sdev^2) / sum(pca$sdev^2)
      load <- abs(pca$rotation) %*% matrix(ve, ncol = 1)
      pca_sc <- as.vector(load)
      names(pca_sc) <- rownames(pca$rotation)
      pca_imp$pca[pca_imp$feature %in% names(pca_sc)] <- pca_sc[pca_imp$feature[pca_imp$feature %in% names(pca_sc)]]
    }
  }
  
  # Combine
  imp <- list(
    corr = corr_tbl %>% mutate(corr = rescale_01(corr)),
    anova = anova_tbl %>% mutate(anova_f = rescale_01(anova_f)),
    chisq = chisq_tbl %>% mutate(chisq = rescale_01(chisq)),
    pca  = pca_imp %>% mutate(pca = rescale_01(pca))
  ) %>% reduce(full_join, by = "feature") %>%
    mutate(across(-feature, ~replace_na(., 0))) %>%
    mutate(score_aggregate = rowMeans(across(-feature), na.rm = TRUE)) %>%
    arrange(desc(score_aggregate))
  
  if (!is.null(max_features)) imp <- imp %>% slice_head(n = max_features)
  imp
}

## ==================== 10. Dimensionality Reduction (PCA) ================= ##
run_dimensionality_reduction <- function(X_scaled, max_pcs = 10) {
  Xc <- scale(X_scaled, center = TRUE, scale = FALSE)
  p <- prcomp(Xc, center = FALSE, scale. = FALSE)
  k <- min(max_pcs, ncol(p$x))
  list(scores = p$x[, seq_len(k), drop = FALSE], model = p, pcs = k, var_explained = (p$sdev^2)/sum(p$sdev^2))
}

## =================== 11. Choose K: gap, silhouette, elbow ================= ##
choose_k_multi <- function(X_reduced, max_k = 50) {
  n <- nrow(X_reduced)
  max_k <- max(2, min(max_k, n - 1, 20))  # safety
  
  # Gap statistic
  gap <- cluster::clusGap(X_reduced, FUN = kmeans, K.max = max_k, B = 20)
  k_gap <- max(2, which.max(gap$Tab[,"gap"]))
  
  # Silhouette
  sil_scores <- map_dbl(2:max_k, function(k) {
    cl <- kmeans(X_reduced, centers = k, nstart = 10)$cluster
    mean(cluster::silhouette(cl, dist(X_reduced))[,3])
  })
  k_sil <- which.max(sil_scores) + 1
  
  # Elbow (total withinss)
  wss <- map_dbl(1:max_k, function(k) {
    if (k == 1) sum(stats::kmeans(X_reduced, centers = 1, nstart = 5)$withinss)
    else sum(stats::kmeans(X_reduced, centers = k, nstart = 5)$withinss)
  })
  # knee via second derivative approx
  d2 <- diff(diff(wss))
  k_elbow <- which.min(c(Inf, d2, Inf))
  k_elbow <- max(2, min(k_elbow, max_k))
  
  round(mean(c(k_gap, k_sil, k_elbow))) %>% max(2)
}

## ======================= 12. Clustering & Printer ======================== ##

# ---- Neutral labels (drop-in) ----
label_config <- function(
    entity_label  = "entity",      # e.g., "customer", "agent", "SKU", "machine", "campaign"
    plural_label  = NULL,          # if NULL -> entity_label + "s"
    kpi_label     = "KPI",         # e.g., "revenue", "uptime", "AUC", "CTR"
    score_label   = "Potential score (0–100)"
) {
  list(
    entity_label = entity_label,
    plural_label = plural_label %||% paste0(entity_label, "s"),
    kpi_label    = kpi)}

cluster_on_reduced_data <- function(data, reduced_result, selected_features, target_variable, auto_k = TRUE, max_k = 50) {
  Xr <- reduced_result$scores
  k <- if (auto_k) choose_k_multi(Xr, max_k) else min(max_k, 5)
  km <- kmeans(Xr, centers = k, nstart = 50)
  sil <- mean(cluster::silhouette(km$cluster, dist(Xr))[,3])
  
  data_with_clusters <- data %>%
    mutate(cluster_id = km$cluster)
  
  list(
    k = k,
    clusters = km$cluster,
    centers  = km$centers,
    silhouette_mean = sil,
    reduced = reduced_result,
    selected_features = selected_features,
    target_variable = target_variable,
    data_with_clusters = data_with_clusters
  )
}

print_cluster_summary <- function(cluster_result) {
  cat("=== Clustering Summary ===\n")
  cat("Chosen K: ", cluster_result$k, "\n")
  cat("Avg silhouette: ", round(cluster_result$silhouette_mean, 3), "\n")
  cat("\nCluster sizes:\n")
  print(table(cluster_result$clusters))
}

## ====================== 13. Driver Analysis (per cluster) ================= ##
analyze_cluster_drivers <- function(cluster_result, feature_types_df, target_variable, top_n = 20) {
  dfc <- cluster_result$data_with_clusters
  feats <- cluster_result$selected_features
  out <- list()
  for (cl in sort(unique(dfc$cluster_id))) {
    sub <- dfc %>% filter(cluster_id == cl)
    if (nrow(sub) < 10) next
    # build design on selected features
    dm <- build_numeric_design_matrix(sub, feats, feature_types_df)
    X <- dm$X
    y <- sub[[target_variable]]
    if (is.numeric(y)) {
      fit <- try(lm(y ~ X), silent = TRUE)
      imp <- if (!inherits(fit, "try-error")) {
        co <- coef(summary(fit))[-1, , drop = FALSE]
        tibble(feature_idx = seq_len(nrow(co)), t_value = abs(co[, "t value"])) %>%
          mutate(feature = colnames(X)[feature_idx]) %>%
          arrange(desc(t_value)) %>%
          slice_head(n = top_n) %>%
          select(feature, importance = t_value)
      } else tibble(feature = character(0), importance = numeric(0))
    } else {
      imp <- tibble(feature = character(0), importance = numeric(0))
    }
    out[[as.character(cl)]] <- list(cluster = cl, drivers = imp)
  }
  out
}

analyze_global_drivers <- function(cluster_result, feature_types_df, target_variable, selected_features, top_n = 30) {
  df <- cluster_result$data_with_clusters
  dm <- build_numeric_design_matrix(df, selected_features, feature_types_df)
  X <- dm$X; y <- df[[target_variable]]
  if (is.numeric(y)) {
    # use RandomForest importance
    rf <- randomForest(x = X, y = y, ntree = 200, importance = TRUE)
    imp <- importance(rf, type = 1) %>% as.numeric()
    tibble(feature = colnames(X), model_contrib = rescale_01(imp)) %>%
      arrange(desc(model_contrib)) %>% slice_head(n = top_n) -> drivers
  } else {
    drivers <- tibble(feature = character(0), model_contrib = numeric(0))
  }
  list(drivers = drivers)
}

compare_global_cluster_drivers <- function(global_drivers, cluster_driver_results,
                                           importance_hi = 0.2, importance_lo = 0.05, top_n = 10) {
  global_set <- global_drivers$drivers %>% filter(model_contrib >= importance_lo) %>% pull(feature)
  cl_summ <- map_dfr(names(cluster_driver_results), function(k) {
    tibble(cluster = as.integer(k),
           feature = cluster_driver_results[[k]]$drivers$feature,
           cl_importance = cluster_driver_results[[k]]$drivers$importance) %>%
      mutate(is_global = feature %in% global_set)
  })
  list(
    overlaps = cl_summ %>% filter(is_global) %>% group_by(cluster) %>%
      slice_max(order_by = cl_importance, n = top_n) %>% ungroup(),
    cluster_only = cl_summ %>% filter(!is_global) %>%
      group_by(cluster) %>% slice_max(order_by = cl_importance, n = top_n) %>% ungroup()
  )
}

## ================== 14. Multi-method Potential (score + units) =========== ##
compute_potential_percentile <- function(df, cluster_col, target_variable, pct = 0.90) {
  df %>%
    group_by(.data[[cluster_col]]) %>%
    mutate(target_pct = quantile(.data[[target_variable]], probs = pct, na.rm = TRUE)) %>%
    ungroup() %>%
    transmute(!!rlang::sym(cluster_col), .unit_row = row_number(), pct_potential = target_pct)
}

compute_potential_regression <- function(df, feature_types_df, features, target_variable) {
  dm <- build_numeric_design_matrix(df, features, feature_types_df)
  X <- dm$X; y <- df[[target_variable]]
  if (!is.numeric(y)) return(tibble(.unit_row = seq_len(nrow(df)), reg_potential = NA_real_))
  fit <- try(lm(y ~ X), silent = TRUE)
  if (inherits(fit, "try-error")) {
    return(tibble(.unit_row = seq_len(nrow(df)), reg_potential = NA_real_))
  }
  pred <- pmax(predict(fit), 0)
  tibble(.unit_row = seq_len(nrow(df)), reg_potential = pred)
}

compute_potential_ml <- function(df, feature_types_df, features, target_variable) {
  dm <- build_numeric_design_matrix(df, features, feature_types_df)
  X <- dm$X; y <- df[[target_variable]]
  if (!is.numeric(y) || nrow(X) < 20) return(tibble(.unit_row = seq_len(nrow(df)), ml_potential = NA_real_))
  rf <- randomForest(x = X, y = y, ntree = 300)
  pred <- pmax(predict(rf, X), 0)
  tibble(.unit_row = seq_len(nrow(df)), ml_potential = pred)
}

combine_potential_methods <- function(df, unit_id, target_variable, cluster_col,
                                      percentile_tbl, reg_tbl, ml_tbl,
                                      weights = c(percentile = 0.2, regression = 0.4, ml = 0.4)) {
  base <- tibble(.unit_row = seq_len(nrow(df)))
  allp <- base %>%
    left_join(percentile_tbl %>% mutate(.unit_row = row_number()) %>% select(.unit_row, pct_potential),
              by = ".unit_row") %>%
    left_join(reg_tbl, by = ".unit_row") %>%
    left_join(ml_tbl, by = ".unit_row")
  
  # Convert percentile from cluster benchmark to a "should-be" in units:
  # conservative: potential_units = max(current, weighted estimate)
  current <- df[[target_variable]]
  
  # consensus units: weighted average of available methods, using current if method missing
  w <- weights / sum(weights)
  pot_units <- rowMeans(
    cbind(
      if (!all(is.na(allp$pct_potential))) allp$pct_potential else current,
      if (!all(is.na(allp$reg_potential))) allp$reg_potential else current,
      if (!all(is.na(allp$ml_potential))) allp$ml_potential else current
    ) %*% diag(c(w["percentile"] %||% 0, w["regression"] %||% 0, w["ml"] %||% 0)),
    na.rm = TRUE
  )
  
  # ensure potential is at least current (headroom only)
  pot_units <- pmax(pot_units, current)
  
  # potential score 0-100 based on rank vs others’ headroom
  uplift <- pot_units - current
  score <- rescale_01(uplift) * 100
  
  tibble(
    .unit_row = seq_len(nrow(df)),
    !!sym(unit_id) := df[[unit_id]],
    current_target = current,
    potential_units = pot_units,
    uplift_units = uplift,
    potential_score_0_100 = score,
    cluster_id = df[[cluster_col]]
  )
}

## ======================== 15. Summary Table Builder ====================== ##
build_dimension_summary <- function(cluster_result, multi_potential,
                                    cluster_driver_results, comparison_results,
                                    unit_id, target_variable) {
  
  drivers_by_cluster <- map_dfr(names(cluster_driver_results), function(k) {
    tibble(cluster_id = as.integer(k),
           main_drivers = paste(head(cluster_driver_results[[k]]$drivers$feature, 5), collapse = ", "))
  })
  
  potentials <- multi_potential %>%
    rename(current_target_mean = current_target,
           should_be_target_mean = potential_units) %>%
    mutate(uplift_in_units = uplift_units)
  
  df_out <- cluster_result$data_with_clusters %>%
    mutate(.unit_row = row_number()) %>%
    select(.unit_row, !!sym(unit_id), cluster_id, !!sym(target_variable)) %>%
    left_join(potentials %>% select(.unit_row, potential_score_0_100, uplift_in_units,
                                    should_be_target_mean, current_target_mean, cluster_id),
              by = c(".unit_row","cluster_id")) %>%
    left_join(drivers_by_cluster, by = "cluster_id") %>%
    select(
      !!sym(unit_id), cluster_id,
      current_target_mean, should_be_target_mean, uplift_in_units,
      potential_score_0_100, main_drivers
    )
  
  df_out
}

## ====================== 16. Orchestrator (core engine) =================== ##
run_infinite_dimensions <- function(data_source, config) {
  target_variable <- config$target_variable
  unit_id         <- config$unit_id
  
  
  # ---- Neutral labels (drop-in) ----
  label_config <- function(
    entity_label  = "entity",      # e.g., "customer", "agent", "SKU", "machine", "campaign"
    plural_label  = NULL,          # if NULL -> entity_label + "s"
    kpi_label     = "KPI",         # e.g., "revenue", "uptime", "AUC", "CTR"
    score_label   = "Potential score (0–100)"
  ) {
    list(
      entity_label = entity_label,
      plural_label = plural_label %||% paste0(entity_label, "s"),
      kpi_label    = kpi)}
  
  
  # 1) Load (single or multiple) + auto-merge
  if (is.list(data_source) || (is.atomic(data_source) && length(data_source) > 1)) {
    mr <- load_many_and_merge(data_source)
    data <- mr$data
    merge_report <- mr
  } else {
    data <- load_data_agnostic(data_source)
    merge_report <- NULL
  }

  
  # 2) Feature types
  ftypes <- detect_feature_types(data, target_variable)
  
  # 3) Geo detect + geocode (if needed) + geo features
  geo_vars <- detect_geospatial_variables(data)
  data_geo <- geocode_if_needed(data, geo_vars)
  # re-detect lat/lon after geocoding
  geo_vars2 <- detect_geospatial_variables(data_geo)
  lat_col <- geo_vars2$latitude[1] %||% if ("lat" %in% names(data_geo)) "lat" else NULL
  lon_col <- geo_vars2$longitude[1] %||% if ("lon" %in% names(data_geo)) "lon" else NULL
  data_geo <- add_geo_features(data_geo, lat_col, lon_col, radii_km = c(1, 5))
  
  # 4) Candidate features (exclude target/unit)
  base_features <- setdiff(names(data_geo), c(target_variable, unit_id))
  
  # 5) Multi-method feature importance & selection
  imp <- feature_importance_multi(
    data = data_geo,
    feature_types_df = ftypes,
    features = base_features,
    target_variable = target_variable,
    max_features = config$feature$max_features
  )
  selected_features <- imp$feature
  
  # 6) Design matrix + scaling
  dm <- build_numeric_design_matrix(data_geo, selected_features, ftypes)
  X_all <- dm$X
  scaling_method <- config$scaling$force_method %||% recommend_scaling_method(X_all)
  X_scaled <- apply_feature_scaling(X_all, method = scaling_method)
  
  # 7) PCA
  red <- run_dimensionality_reduction(X_scaled, max_pcs = config$dimred$max_pcs)
  
  # 8) Clustering
  cl <- cluster_on_reduced_data(
    data = data_geo,
    reduced_result = red,
    selected_features = selected_features,
    target_variable = target_variable,
    auto_k = config$clustering$auto_k,
    max_k  = config$clustering$max_clusters
  )
  print_cluster_summary(cl)
  
  # 9) Drivers (cluster-level + global)
  cluster_drivers <- analyze_cluster_drivers(
    cluster_result = cl,
    feature_types_df = ftypes,
    target_variable = target_variable,
    top_n = config$drivers$top_n_cluster
  )
  global_drivers <- analyze_global_drivers(
    cluster_result = cl,
    feature_types_df = ftypes,
    target_variable = target_variable,
    selected_features = selected_features,
    top_n = config$drivers$top_n_global
  )
  comparison_results <- compare_global_cluster_drivers(global_drivers, cluster_drivers)
  
  # 10) Multi-method potential
  dfc <- cl$data_with_clusters
  pct_tbl <- compute_potential_percentile(
    df = dfc, cluster_col = "cluster_id", target_variable = target_variable,
    pct = config$potential$cluster_percentile_target
  )
  reg_tbl <- if (config$potential$use_regression)
    compute_potential_regression(dfc, ftypes, selected_features, target_variable) else
      tibble(.unit_row = seq_len(nrow(dfc)), reg_potential = NA_real_)
  ml_tbl  <- if (config$potential$use_ml)
    compute_potential_ml(dfc, ftypes, selected_features, target_variable) else
      tibble(.unit_row = seq_len(nrow(dfc)), ml_potential = NA_real_)
  
  wts <- c(
    percentile = if (config$potential$use_percentile) config$potential$percentile_weight else 0,
    regression = if (config$potential$use_regression) config$potential$regression_weight else 0,
    ml         = if (config$potential$use_ml)         config$potential$ml_weight         else 0
  )
  
  multi_potential <- combine_potential_methods(
    df = dfc, unit_id = unit_id, target_variable = target_variable, cluster_col = "cluster_id",
    percentile_tbl = pct_tbl, reg_tbl = reg_tbl, ml_tbl = ml_tbl, weights = wts
  )
  
  # 11) Summary table
  summary_tbl <- build_dimension_summary(
    cluster_result = cl,
    multi_potential = multi_potential,
    cluster_driver_results = cluster_drivers,
    comparison_results = comparison_results,
    unit_id = unit_id,
    target_variable = target_variable
  )
  
  list(
    config = config,
    data = data_geo,
    feature_types = ftypes,
    selected_features = selected_features,
    scaling_method = scaling_method,
    reduced = red,
    cluster_result = cl,
    cluster_drivers = cluster_drivers,
    global_drivers = global_drivers,
    comparison_results = comparison_results,
    multi_potential = multi_potential,
    summary_table = summary_tbl
 
    return(list(
      config = config,
      data = data_geo,
      feature_types = ftypes,
      selected_features = selected_features,
      scaling_method = scaling_method,
      reduced = red,
      cluster_result = cl,
      cluster_drivers = cluster_drivers,
      global_drivers = global_drivers,
      comparison_results = comparison_results,
      multi_potential = multi_potential,
      summary_table = summary_tbl,
      merge_report = merge_report   # ← NEW
    ))
}

     )
}

## ========================= 17. Chat/AI Wrapper =========================== ##
run_analysis <- function(data_source,
                         target_variable,
                         unit_id,
                         max_features         = 50,
                         max_pcs              = 10,
                         max_clusters         = 50,
                         auto_k               = TRUE,
                         use_regression       = TRUE,
                         use_ml               = TRUE,
                         use_percentile       = TRUE,
                         regression_weight    = 0.4,
                         ml_weight            = 0.4,
                         percentile_weight    = 0.2,
                         cluster_pct_target   = 0.90,
                         force_scaling_method = NULL) {
  cfg <- make_analytics_config(
    target_variable          = target_variable,
    unit_id                  = unit_id,
    max_features             = max_features,
    max_pcs                  = max_pcs,
    max_clusters             = max_clusters,
    auto_k                   = auto_k,
    use_regression           = use_regression,
    use_ml                   = use_ml,
    use_percentile           = use_percentile,
    regression_weight        = regression_weight,
    ml_weight                = ml_weight,
    percentile_weight        = percentile_weight,
    cluster_percentile_target = cluster_pct_target,
    force_scaling_method     = force_scaling_method
  )
  result <- run_infinite_dimensions(data_source, cfg)
  result$index <- list(
    target_variable = target_variable,
    unit_id = unit_id,
    n_units = nrow(result$summary_table),
    n_clusters = length(unique(result$cluster_result$data_with_clusters$cluster_id)),
    scaling_method = result$scaling_method
  )
  result
}

answer_question <- function(result, question, top_n = 5) {
  q <- tolower(question)
  summary_tbl <- result$summary_table
  unit_id     <- result$config$unit_id
  target_var  <- result$config$target_variable
  
  if (grepl("highest potential|top potential|biggest opportunity", q)) {
    out <- summary_tbl %>%
      slice_max(order_by = potential_score_0_100, n = top_n)
    return(list(
      type = "table",
      intent = "top_potential_units",
      message = paste0("Top ", top_n, " ", unit_id, " by potential score for '", target_var, "'."),
      data = out
    ))
  }
  
  if (grepl("explain|why|driver|drivers", q) && grepl(unit_id, q)) {
    candidate <- stringr::str_extract(q, "(\\d+|\"[^\"]+\"|'[^']+')") %>% gsub("[\"']", "", .)
    if (!is.na(candidate)) {
      row <- summary_tbl %>% filter(.data[[unit_id]] == candidate)
      if (nrow(row)) {
        msg <- paste0(
          unit_id, " ", candidate, ": current ", target_var, " = ", round(row$current_target_mean, 1),
          ", should-be = ", round(row$should_be_target_mean, 1),
          ", uplift ≈ ", round(row$uplift_in_units, 1),
          ", potential score = ", round(row$potential_score_0_100, 1),
          ". Drivers: ", row$main_drivers
        )
        return(list(type = "text", intent = "unit_explanation", message = msg))
      }
    }
  }
  
  if (grepl("main driver|key driver|overall driver", q)) {
    g <- result$global_drivers$drivers %>% slice_max(order_by = model_contrib, n = top_n)
    txt <- paste0("Top ", top_n, " global drivers of '", target_var, "':\n",
                  paste0("- ", g$feature, " (≈ ", round(g$model_contrib, 2), ")", collapse = "\n"))
    return(list(type = "text", intent = "global_drivers", message = txt, data = g))
  }
  
  if (grepl("cluster", q) && grepl("explain|describe|character|profile", q)) {
    cl_num <- stringr::str_extract(q, "\\d+") %>% as.integer()
    if (!is.na(cl_num)) {
      cluster_row <- summary_tbl %>% filter(cluster_id == cl_num)
      if (nrow(cluster_row)) {
        mean_lift <- cluster_row %>% summarise(
          avg_uplift = mean(uplift_in_units, na.rm = TRUE),
          avg_score  = mean(potential_score_0_100, na.rm = TRUE),
          n_units    = n()
        )
        drv <- result$cluster_drivers[[as.character(cl_num)]]$drivers
        msg <- paste0(
          "Cluster ", cl_num, " (", mean_lift$n_units, " ", unit_id, "): avg uplift ",
          round(mean_lift$avg_uplift, 1), " ", target_var, ", avg potential score ",
          round(mean_lift$avg_score, 1), ".\nTop drivers:\n",
          paste0("- ", head(drv$feature, top_n), collapse = "\n")
        )
        return(list(type = "text", intent = "cluster_profile", message = msg, data = drv))
      }
    }
  }
  
  msg <- paste0(
    "Analyzed target '", target_var, "' across ", nrow(summary_tbl), " ", unit_id,
    " and ", length(unique(summary_tbl$cluster_id)), " clusters.\n",
    "Avg potential score: ", round(mean(summary_tbl$potential_score_0_100, na.rm = TRUE), 1),
    " (max ", round(max(summary_tbl$potential_score_0_100, na.rm = TRUE), 1), ")."
  )
  list(type = "text", intent = "generic_summary", message = msg)
}

## ========================= 18. Solution Templates ======================== ##
make_store_network_template <- function(target = "sales", unit_id = "store_id") {
  make_analytics_config(
    target_variable = target, unit_id = unit_id,
    max_features = 60, max_pcs = 10, max_clusters = 30, auto_k = TRUE,
    top_n_cluster_drivers = 20, top_n_global_drivers = 30,
    use_regression = TRUE, use_ml = TRUE, use_percentile = TRUE,
    regression_weight = 0.4, ml_weight = 0.4, percentile_weight = 0.2,
    cluster_percentile_target = 0.90, force_scaling_method = NULL
  )
}
make_customer_segmentation_template <- function(target = "revenue", unit_id = "customer_id") {
  make_analytics_config(
    target_variable = target, unit_id = unit_id,
    max_features = 80, max_pcs = 15, max_clusters = 40, auto_k = TRUE,
    top_n_cluster_drivers = 25, top_n_global_drivers = 40,
    use_regression = TRUE, use_ml = TRUE, use_percentile = TRUE,
    regression_weight = 0.3, ml_weight = 0.5, percentile_weight = 0.2,
    cluster_percentile_target = 0.95, force_scaling_method = "standardize"
  )
}
make_campaign_performance_template <- function(target = "roi", unit_id = "campaign_id") {
  make_analytics_config(
    target_variable = target, unit_id = unit_id,
    max_features = 40, max_pcs = 8, max_clusters = 20, auto_k = TRUE,
    top_n_cluster_drivers = 15, top_n_global_drivers = 25,
    use_regression = TRUE, use_ml = TRUE, use_percentile = TRUE,
    regression_weight = 0.5, ml_weight = 0.3, percentile_weight = 0.2,
    cluster_percentile_target = 0.90, force_scaling_method = "robust"
  )
}

## ============================== 19. Usage ================================ ##
# Example:
# cfg <- make_store_network_template(target = "sales", unit_id = "store_id")
# res <- run_infinite_dimensions("stores.csv", cfg)
# head(res$summary_table)
# ans <- answer_question(res, "Which store_id has the highest potential?")
# ans$message

