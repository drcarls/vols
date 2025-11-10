
library(tidyverse)
library(cluster)
library(dbscan)
library(recipes)
library(rsample)
library(purrr)
library(furrr)
library(foreach)
library(doParallel)

# Enable parallel processing
plan(multisession, workers = parallel::detectCores() - 1)

# Infinite Dimensions Configuration
INFINITE_DIM_CONFIG <- list(
  # Dynamic discovery
  auto_detect_features = TRUE,
  max_features = NULL,  # NULL = no limit
  feature_importance_threshold = 0.01,
  
  # Adaptive clustering
  auto_determine_clusters = TRUE,
  max_clusters = 50,
  cluster_quality_threshold = 0.7,
  
  # Dynamic analysis
  correlation_threshold = 0.3,
  min_sample_size = 10,
  
  # Resource management
  chunk_size = 1000,  # Process features in chunks
  max_memory_gb = 8
)

load_data_agnostic <- function(data_source, target_col = NULL) {
  # Handle multiple data source types
  if (is.character(data_source)) {
    if (grepl("\\.csv$", data_source)) {
      data <- read_csv(data_source, show_col_types = FALSE)
    } else if (grepl("\\.xlsx$", data_source)) {
      data <- readxl::read_excel(data_source)
    } else if (grepl("\\.json$", data_source)) {
      data <- jsonlite::read_json(data_source, simplifyVector = TRUE)
    } else {
      stop("Unsupported file format")
    }
  } else if (is.data.frame(data_source)) {
    data <- data_source
  } else {
    stop("Data source must be file path or data frame")
  }
  
  # Auto-detect feature types
  feature_info <- analyze_features(data, target_col)
  
  return(list(
    data = data,
    features = feature_info$features,
    feature_types = feature_info$types,
    target = target_col
  ))
}

analyze_features <- function(data, target_col = NULL) {
  features <- setdiff(names(data), target_col)
  
  feature_types <- map_chr(features, function(feature) {
    if (is.numeric(data[[feature]])) {
      if (length(unique(data[[feature]])) / nrow(data) < 0.05) {
        "low_cardinality_numeric"
      } else {
        "continuous_numeric"
      }
    } else if (is.character(data[[feature]]) | is.factor(data[[feature]])) {
      if (length(unique(data[[feature]])) / nrow(data) < 0.1) {
        "categorical"
      } else {
        "high_cardinality_categorical"
      }
    } else if (is.logical(data[[feature]])) {
      "boolean"
    } else if (lubridate::is.Date(data[[feature]]) | lubridate::is.POSIXt(data[[feature]])) {
      "temporal"
    } else {
      "unknown"
    }
  })
  
  list(
    features = features,
    types = setNames(feature_types, features)
  )
}

