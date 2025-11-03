###########################################
# Plot changes in college attainment across states
# Collin Wardius                          #
# August 15, 2025                            #
###########################################

library(ggplot2)
library(dplyr)
library(maps)
library(viridis)
library(gridExtra)
library(grid)
library(cowplot)
library(stringr)
library(tidyr)
library(scales)
library(readxl)

setwd('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education')
data <- read.csv('data/clean/cohort_col_by_state.csv')
other_data <- read_excel('data/clean/total_public_enroll_1937_38.xlsx') %>% 
  mutate(bpl=tolower(state))

data <- data %>% inner_join(other_data, by='bpl')
# Define continental US states (excluding Alaska, Hawaii, and DC)
continental_states <- c(
  "alabama", "arizona", "arkansas", "california", "colorado", "connecticut", 
  "delaware", "florida", "georgia", "idaho", "illinois", "indiana", "iowa", 
  "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", 
  "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska", 
  "nevada", "new hampshire", "new jersey", "new mexico", "new york", 
  "north carolina", "north dakota", "ohio", "oklahoma", "oregon", 
  "pennsylvania", "rhode island", "south carolina", "south dakota", 
  "tennessee", "texas", "utah", "vermont", "virginia", "washington", 
  "west virginia", "wisconsin", "wyoming"
)

# Get state map data for continental US
states_map <- map_data("state")

# Filter for continental US and specified years
years_of_interest <- c(1900, 1910, 1920, 1930, 1936)

filtered_data <- data %>%
  filter(bpl %in% continental_states,
         est_hs_grad_year %in% years_of_interest) %>%
  rename(region = bpl)  # Rename to match map data

# Calculate consistent scales for both metrics across all years
ba_range <- range(filtered_data$ba_or_above, na.rm = TRUE)
college_range <- range(filtered_data$any_college, na.rm = TRUE)

# Create common map theme
map_theme <- theme_void() +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5),
    legend.position = "bottom",
    legend.title = element_text(size = 10),
    legend.text = element_text(size = 8),
    strip.text = element_text(size = 12, face = "bold"),
    panel.spacing = unit(0.5, "lines")
  )

# Function to create maps
create_education_maps <- function(metric_col, metric_name, color_scale, file_suffix) {
  
  # Merge data with map coordinates
  map_data_merged <- states_map %>%
    left_join(filtered_data, by = "region")
  
  # Create the map
  p <- ggplot(map_data_merged, aes(x = long, y = lat, group = group)) +
    geom_polygon(aes_string(fill = metric_col), color = "white", size = 0.2) +
    facet_wrap(~ est_hs_grad_year, ncol = 3,
               labeller = labeller(est_hs_grad_year = function(x) paste("Year:", x))) +
    coord_fixed(1.3) +
    labs(
      title = paste(metric_name, "by State and Year"),
      subtitle = "Continental United States: 1900, 1910, 1920, 1930, 1936",
      fill = metric_name,
      caption = "Data: College education rates by birth state and estimated graduation year"
    ) +
    color_scale +
    map_theme
  
  return(p)
}

# 1. Bachelor's Degree Completion Maps
print("Creating Bachelor's Degree Completion maps...")

ba_scale <- scale_fill_gradient(
  low = "lightblue", 
  high = "darkblue",
  limits = ba_range,
  na.value = "grey90",
  labels = scales::percent_format(accuracy = 0.1)
)

p1 <- create_education_maps("ba_or_above", "BA Completion Rate", ba_scale, "ba")
print(p1)

# 2. Any College Attendance Maps
print("Creating Any College Attendance maps...")

college_scale <- scale_fill_gradient(
  low = "lightgreen", 
  high = "darkgreen",
  limits = college_range,
  na.value = "grey90",
  labels = scales::percent_format(accuracy = 0.1)
)

p2 <- create_education_maps("any_college", "Any College Rate", college_scale, "college")
print(p2)

# 3. Side-by-side comparison for a specific year (1930 as example)
print("Creating side-by-side comparison for 1930...")

data_1930 <- filtered_data %>% filter(est_hs_grad_year == 1930)

map_data_1930 <- states_map %>%
  left_join(data_1930, by = "region")

# BA completion 1930
p3a <- ggplot(map_data_1930, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_or_above), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "BA Completion Rate - 1930") +
  scale_fill_gradient(
    low = "lightblue", 
    high = "darkblue",
    limits = ba_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "BA Rate"
  ) +
  map_theme

# Any college 1930
p3b <- ggplot(map_data_1930, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = any_college), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Any College Rate - 1930") +
  scale_fill_gradient(
    low = "lightgreen", 
    high = "darkgreen",
    limits = college_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "College Rate"
  ) +
  map_theme

# Combine plots side by side (requires gridExtra or patchwork)
library(gridExtra)
p3 <- grid.arrange(p3a, p3b, ncol = 2, 
                   top = "Education Rates Comparison - 1930")
print(p3)

# 4. Change Maps: 1900 to 1936
print("Creating change maps...")

# Calculate changes between 1900 and 1936
change_data <- data %>%
  filter(bpl %in% continental_states,
         est_hs_grad_year %in% c(1900, 1936)) %>%
  rename(region = bpl) %>%
  select(region, est_hs_grad_year, ba_or_above, any_college) %>%
  pivot_wider(names_from = est_hs_grad_year, 
              values_from = c(ba_or_above, any_college),
              names_sep = "_") %>%
  mutate(
    ba_change = ba_or_above_1936 - ba_or_above_1900,
    college_change = any_college_1936 - any_college_1900
  ) %>%
  select(region, ba_change, college_change)

# Calculate ranges for change maps
ba_change_range <- range(change_data$ba_change, na.rm = TRUE)
college_change_range <- range(change_data$college_change, na.rm = TRUE)

# Merge change data with map coordinates
map_data_change <- states_map %>%
  left_join(change_data, by = "region")

# BA completion change map
p4a <- ggplot(map_data_change, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_change), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Change in BA Completion Rate (1900 to 1936)") +
  scale_fill_gradient(
    low = "lightyellow", 
    high = "darkred",
    limits = ba_change_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "Change in\nBA Rate"
  ) +
  map_theme

# Any college change map
p4b <- ggplot(map_data_change, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = college_change), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Change in Any College Rate (1900 to 1936)") +
  scale_fill_gradient(
    low = "lightcyan", 
    high = "darkblue",
    limits = college_change_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "Change in\nCollege Rate"
  ) +
  map_theme

# Combine change plots side by side
p4 <- grid.arrange(p4a, p4b, ncol = 2, 
                   top = "Changes in Education Rates: 1900 to 1936")
print(p4)

# 5. Percentage Change Maps: 1900 to 1936
print("Creating percentage change maps...")

# Calculate percentage changes between 1900 and 1936
pct_change_data <- data %>%
  filter(bpl %in% continental_states,
         est_hs_grad_year %in% c(1900, 1936)) %>%
  rename(region = bpl) %>%
  select(region, est_hs_grad_year, ba_or_above, any_college) %>%
  pivot_wider(names_from = est_hs_grad_year, 
              values_from = c(ba_or_above, any_college),
              names_sep = "_") %>%
  mutate(
    ba_pct_change = ifelse(ba_or_above_1900 > 0, 
                           (ba_or_above_1936 - ba_or_above_1900) / ba_or_above_1900 * 100,
                           NA),
    college_pct_change = ifelse(any_college_1900 > 0,
                                (any_college_1936 - any_college_1900) / any_college_1900 * 100,
                                NA)
  ) %>%
  select(region, ba_pct_change, college_pct_change)

# Calculate ranges for percentage change maps
ba_pct_range <- range(pct_change_data$ba_pct_change, na.rm = TRUE)
college_pct_range <- range(pct_change_data$college_pct_change, na.rm = TRUE)

# Merge percentage change data with map coordinates
map_data_pct_change <- states_map %>%
  left_join(pct_change_data, by = "region")

# BA completion percentage change map
p5a <- ggplot(map_data_pct_change, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_pct_change), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Percentage Change in BA Completion Rate (1900 to 1936)") +
  scale_fill_gradient(
    low = "lightpink", 
    high = "darkmagenta",
    limits = ba_pct_range,
    na.value = "grey90",
    labels = function(x) paste0(round(x, 0), "%"),
    name = "% Change in\nBA Rate"
  ) +
  map_theme

# Any college percentage change map
p5b <- ggplot(map_data_pct_change, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = college_pct_change), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Percentage Change in Any College Rate (1900 to 1936)") +
  scale_fill_gradient(
    low = "lightsteelblue", 
    high = "navy",
    limits = college_pct_range,
    na.value = "grey90",
    labels = function(x) paste0(round(x, 0), "%"),
    name = "% Change in\nCollege Rate"
  ) +
  map_theme

# Combine percentage change plots side by side
p5 <- grid.arrange(p5a, p5b, ncol = 2, 
                   top = "Percentage Changes in Education Rates: 1900 to 1936")
print(p5)

# 6. Before and After Comparison Maps: 1900 vs 1936
print("Creating before and after comparison maps...")

# Get data for 1900 and 1936
data_1900 <- filtered_data %>% filter(est_hs_grad_year == 1900)
data_1936 <- filtered_data %>% filter(est_hs_grad_year == 1936)

# Merge with map data
map_data_1900 <- states_map %>% left_join(data_1900, by = "region")
map_data_1936 <- states_map %>% left_join(data_1936, by = "region")

# BA Completion: 1900 vs 1936 comparison
p6a_1900 <- ggplot(map_data_1900, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_or_above), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "BA Completion Rate - 1900") +
  scale_fill_gradient(
    low = "lightblue", 
    high = "darkblue",
    limits = ba_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "BA Rate"
  ) +
  map_theme

p6a_1936 <- ggplot(map_data_1936, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_or_above), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "BA Completion Rate - 1936") +
  scale_fill_gradient(
    low = "lightblue", 
    high = "darkblue",
    limits = ba_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "BA Rate"
  ) +
  map_theme

# Combine BA comparison plots
p6a <- grid.arrange(p6a_1900, p6a_1936, ncol = 2, 
                    top = "BA Completion Rate Comparison: 1900 vs 1936")
print(p6a)

# Any College: 1900 vs 1936 comparison
p6b_1900 <- ggplot(map_data_1900, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = any_college), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Any College Rate - 1900") +
  scale_fill_gradient(
    low = "lightgreen", 
    high = "darkgreen",
    limits = college_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "College Rate"
  ) +
  map_theme

p6b_1936 <- ggplot(map_data_1936, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = any_college), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Any College Rate - 1936") +
  scale_fill_gradient(
    low = "lightgreen", 
    high = "darkgreen",
    limits = college_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "College Rate"
  ) +
  map_theme

# Combine Any College comparison plots
p6b <- grid.arrange(p6b_1900, p6b_1936, ncol = 2, 
                    top = "Any College Rate Comparison: 1900 vs 1936")
print(p6b)

################################################################################
# CONDITIONAL ON HIGH SCHOOL MAPS
################################################################################

# Calculate consistent scales for conditional metrics across all years
ba_cond_range <- range(filtered_data$ba_or_above_cond_hs, na.rm = TRUE)
college_cond_range <- range(filtered_data$any_college_cond_hs, na.rm = TRUE)

# 7. Bachelor's Degree Completion Maps (Conditional on HS)
print("Creating Bachelor's Degree Completion maps (conditional on HS)...")

ba_cond_scale <- scale_fill_gradient(
  low = "lightblue", 
  high = "darkblue",
  limits = ba_cond_range,
  na.value = "grey90",
  labels = scales::percent_format(accuracy = 0.1)
)

p7 <- create_education_maps("ba_or_above_cond_hs", "BA Completion Rate (Conditional on HS)", ba_cond_scale, "ba_cond")
print(p7)

# 8. Any College Attendance Maps (Conditional on HS)
print("Creating Any College Attendance maps (conditional on HS)...")

college_cond_scale <- scale_fill_gradient(
  low = "lightgreen", 
  high = "darkgreen",
  limits = college_cond_range,
  na.value = "grey90",
  labels = scales::percent_format(accuracy = 0.1)
)

p8 <- create_education_maps("any_college_cond_hs", "Any College Rate (Conditional on HS)", college_cond_scale, "college_cond")
print(p8)

# 9. Side-by-side comparison for 1930 (Conditional on HS)
print("Creating side-by-side comparison for 1930 (conditional on HS)...")

# BA completion 1930 (conditional on HS)
p9a <- ggplot(map_data_1930, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_or_above_cond_hs), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "BA Completion Rate - 1930 (Conditional on HS)") +
  scale_fill_gradient(
    low = "lightblue", 
    high = "darkblue",
    limits = ba_cond_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "BA Rate\n(Cond. HS)"
  ) +
  map_theme

# Any college 1930 (conditional on HS)
p9b <- ggplot(map_data_1930, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = any_college_cond_hs), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Any College Rate - 1930 (Conditional on HS)") +
  scale_fill_gradient(
    low = "lightgreen", 
    high = "darkgreen",
    limits = college_cond_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "College Rate\n(Cond. HS)"
  ) +
  map_theme

# Combine plots side by side
p9 <- grid.arrange(p9a, p9b, ncol = 2, 
                   top = "Education Rates Comparison - 1930 (Conditional on HS)")
print(p9)

# 10. Change Maps: 1900 to 1936 (Conditional on HS)
print("Creating change maps (conditional on HS)...")

# Calculate changes between 1900 and 1936 for conditional variables
change_data_cond <- data %>%
  filter(bpl %in% continental_states,
         est_hs_grad_year %in% c(1900, 1936)) %>%
  rename(region = bpl) %>%
  select(region, est_hs_grad_year, ba_or_above_cond_hs, any_college_cond_hs) %>%
  pivot_wider(names_from = est_hs_grad_year, 
              values_from = c(ba_or_above_cond_hs, any_college_cond_hs),
              names_sep = "_") %>%
  mutate(
    ba_change_cond = ba_or_above_cond_hs_1936 - ba_or_above_cond_hs_1900,
    college_change_cond = any_college_cond_hs_1936 - any_college_cond_hs_1900
  ) %>%
  select(region, ba_change_cond, college_change_cond)

# Calculate ranges for change maps
ba_change_cond_range <- range(change_data_cond$ba_change_cond, na.rm = TRUE)
college_change_cond_range <- range(change_data_cond$college_change_cond, na.rm = TRUE)

# Merge change data with map coordinates
map_data_change_cond <- states_map %>%
  left_join(change_data_cond, by = "region")

# BA completion change map (conditional on HS)
p10a <- ggplot(map_data_change_cond, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_change_cond), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Change in BA Completion Rate (1900 to 1936) - Conditional on HS") +
  scale_fill_gradient(
    low = "lightyellow", 
    high = "darkred",
    limits = ba_change_cond_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "Change in\nBA Rate\n(Cond. HS)"
  ) +
  map_theme

# Any college change map (conditional on HS)
p10b <- ggplot(map_data_change_cond, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = college_change_cond), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Change in Any College Rate (1900 to 1936) - Conditional on HS") +
  scale_fill_gradient(
    low = "lightcyan", 
    high = "darkblue",
    limits = college_change_cond_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "Change in\nCollege Rate\n(Cond. HS)"
  ) +
  map_theme

# Combine change plots side by side
p10 <- grid.arrange(p10a, p10b, ncol = 2, 
                    top = "Changes in Education Rates: 1900 to 1936 (Conditional on HS)")
print(p10)

# 11. Percentage Change Maps: 1900 to 1936 (Conditional on HS)
print("Creating percentage change maps (conditional on HS)...")

# Calculate percentage changes between 1900 and 1936 for conditional variables
pct_change_data_cond <- data %>%
  filter(bpl %in% continental_states,
         est_hs_grad_year %in% c(1900, 1936)) %>%
  rename(region = bpl) %>%
  select(region, est_hs_grad_year, ba_or_above_cond_hs, any_college_cond_hs) %>%
  pivot_wider(names_from = est_hs_grad_year, 
              values_from = c(ba_or_above_cond_hs, any_college_cond_hs),
              names_sep = "_") %>%
  mutate(
    ba_pct_change_cond = ifelse(ba_or_above_cond_hs_1900 > 0, 
                                (ba_or_above_cond_hs_1936 - ba_or_above_cond_hs_1900) / ba_or_above_cond_hs_1900 * 100,
                                NA),
    college_pct_change_cond = ifelse(any_college_cond_hs_1900 > 0,
                                     (any_college_cond_hs_1936 - any_college_cond_hs_1900) / any_college_cond_hs_1900 * 100,
                                     NA)
  ) %>%
  select(region, ba_pct_change_cond, college_pct_change_cond)

# Calculate ranges for percentage change maps
ba_pct_cond_range <- range(pct_change_data_cond$ba_pct_change_cond, na.rm = TRUE)
college_pct_cond_range <- range(pct_change_data_cond$college_pct_change_cond, na.rm = TRUE)

# Merge percentage change data with map coordinates
map_data_pct_change_cond <- states_map %>%
  left_join(pct_change_data_cond, by = "region")

# BA completion percentage change map (conditional on HS)
p11a <- ggplot(map_data_pct_change_cond, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_pct_change_cond), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Percentage Change in BA Completion Rate (1900 to 1936) - Conditional on HS") +
  scale_fill_gradient(
    low = "lightpink", 
    high = "darkmagenta",
    limits = ba_pct_cond_range,
    na.value = "grey90",
    labels = function(x) paste0(round(x, 0), "%"),
    name = "% Change in\nBA Rate\n(Cond. HS)"
  ) +
  map_theme

# Any college percentage change map (conditional on HS)
p11b <- ggplot(map_data_pct_change_cond, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = college_pct_change_cond), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Percentage Change in Any College Rate (1900 to 1936) - Conditional on HS") +
  scale_fill_gradient(
    low = "lightsteelblue", 
    high = "navy",
    limits = college_pct_cond_range,
    na.value = "grey90",
    labels = function(x) paste0(round(x, 0), "%"),
    name = "% Change in\nCollege Rate\n(Cond. HS)"
  ) +
  map_theme

# Combine percentage change plots side by side
p11 <- grid.arrange(p11a, p11b, ncol = 2, 
                    top = "Percentage Changes in Education Rates: 1900 to 1936 (Conditional on HS)")
print(p11)

# 12. Before and After Comparison Maps: 1900 vs 1936 (Conditional on HS)
print("Creating before and after comparison maps (conditional on HS)...")

# BA Completion: 1900 vs 1936 comparison (conditional on HS)
p12a_1900 <- ggplot(map_data_1900, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_or_above_cond_hs), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "BA Completion Rate - 1900 (Conditional on HS)") +
  scale_fill_gradient(
    low = "lightblue", 
    high = "darkblue",
    limits = ba_cond_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "BA Rate\n(Cond. HS)"
  ) +
  map_theme

p12a_1936 <- ggplot(map_data_1936, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = ba_or_above_cond_hs), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "BA Completion Rate - 1936 (Conditional on HS)") +
  scale_fill_gradient(
    low = "lightblue", 
    high = "darkblue",
    limits = ba_cond_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "BA Rate\n(Cond. HS)"
  ) +
  map_theme

# Combine BA comparison plots (conditional on HS)
p12a <- grid.arrange(p12a_1900, p12a_1936, ncol = 2, 
                     top = "BA Completion Rate Comparison: 1900 vs 1936 (Conditional on HS)")
print(p12a)

# Any College: 1900 vs 1936 comparison (conditional on HS)
p12b_1900 <- ggplot(map_data_1900, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = any_college_cond_hs), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Any College Rate - 1900 (Conditional on HS)") +
  scale_fill_gradient(
    low = "lightgreen", 
    high = "darkgreen",
    limits = college_cond_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "College Rate\n(Cond. HS)"
  ) +
  map_theme

p12b_1936 <- ggplot(map_data_1936, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = any_college_cond_hs), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(title = "Any College Rate - 1936 (Conditional on HS)") +
  scale_fill_gradient(
    low = "lightgreen", 
    high = "darkgreen",
    limits = college_cond_range,
    na.value = "grey90",
    labels = scales::percent_format(accuracy = 0.1),
    name = "College Rate\n(Cond. HS)"
  ) +
  map_theme

# Combine Any College comparison plots (conditional on HS)
p12b <- grid.arrange(p12b_1900, p12b_1936, ncol = 2, 
                     top = "Any College Rate Comparison: 1900 vs 1936 (Conditional on HS)")
print(p12b)


# Create an additional plot that plots the share of public enrollment by state

# Take one value per state (they should all be the same)
share_constant_data <- data %>% 
  subset(est_hs_grad_year==1900) %>% 
  mutate(share_state = state_enrollment / total_enrollment) %>% 
  rename(region=bpl)

# Calculate range
share_range <- range(share_constant_data$share_state, na.rm = TRUE)

# Merge data with map coordinates
map_data_share_constant <- states_map %>%
  left_join(share_constant_data, by = "region")

# Create the single map
p13 <- ggplot(map_data_share_constant, aes(x = long, y = lat, group = group)) +
  geom_polygon(aes(fill = share_state), color = "white", size = 0.2) +
  coord_fixed(1.3) +
  labs(
    title = "Share enrollment in public colleges (1936)",
    fill = "Share public"
  ) +
  scale_fill_gradient(
    low = "lightblue", 
    high = "darkblue",
    limits = share_range,
    na.value = "grey90"
  ) +
  map_theme

print(p13)


# Save plots (optional - uncomment if you want to save)
ggsave("output/figures/ba_completion_maps.png", p1, width = 16, height = 12, dpi = 300)
ggsave("output/figures/college_attendance_maps.png", p2, width = 16, height = 12, dpi = 300)
ggsave("output/figures/education_changes_1900_to_1936.png", p4, width = 14, height = 6, dpi = 300)
ggsave("output/figures/education_percentage_changes_1900_to_1936.png", p5, width = 14, height = 6, dpi = 300)
ggsave("output/figures/ba_completion_1900_vs_1936.png", p6a, width = 14, height = 6, dpi = 300)
ggsave("output/figures/any_college_1900_vs_1936.png", p6b, width = 14, height = 6, dpi = 300)

# Conditional on HS plots
ggsave("output/figures/ba_completion_maps_cond_hs.png", p7, width = 16, height = 12, dpi = 300)
ggsave("output/figures/college_attendance_maps_cond_hs.png", p8, width = 16, height = 12, dpi = 300)
ggsave("output/figures/education_changes_1900_to_1936_cond_hs.png", p10, width = 14, height = 6, dpi = 300)
ggsave("output/figures/education_percentage_changes_1900_to_1936_cond_hs.png", p11, width = 14, height = 6, dpi = 300)
ggsave("output/figures/ba_completion_1900_vs_1936_cond_hs.png", p12a, width = 14, height = 6, dpi = 300)
ggsave("output/figures/any_college_1900_vs_1936_cond_hs.png", p12b, width = 14, height = 6, dpi = 300)
ggsave("output/figures/share_public_enrollment1936.png", p13, width = 16, height = 12, dpi = 300)

