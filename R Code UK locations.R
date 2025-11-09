library(readr)
library(dplyr)
library(gtools)
library(readxl)

#Import dataset 
zipcode_data <- read_excel("UK Demographic Data.xlsx")

zipcode_data1 <- subset(zipcode_data, is.na(Income_Decile)==FALSE)
zipcode_data1 <- subset(zipcode_data1, is.na(Hectares)==FALSE)

#Now create correlation matrix for variables in the dataset to identify those with high correlations - minimize demographic variables
dataforcor <- subset(zipcode_data1, select= c(
  'Asian',
  'Asian_Bangladeshi',
  'Asian_Chinese',
  'Asian_Indian',
  'Asian_Pakistani',
  'Black',
  'Black_African',
  'Black_Caribbean',
  'Black_Other',
  'FEMALE', 
  'Hectares',
  'Income_Decile',
  'Income Score (rate)',
  'MALE', 
  'Med_Age', 
  'Mixed',
  'Other',
  'Other_Arab',
  'Other_Asian',
  'Other_Other',
  'pct_AGE_T0004', 
  'pct_AGE_T0509', 
  'pct_AGE_T1014', 
  'pct_AGE_T1519', 
  'pct_AGE_T2024', 
  'pct_AGE_T2529', 
  'pct_AGE_T3034', 
  'pct_AGE_T3539', 
  'pct_AGE_T4044', 
  'pct_AGE_T4549', 
  'pct_AGE_T5054', 
  'pct_AGE_T5559', 
  'pct_AGE_T6064', 
  'pct_AGE_T6569', 
  'pct_AGE_T7074', 
  'pct_AGE_T75PL',                                          
  'Pop',
  'Pop Density',
  'White'))

cormatrix <- round(cor(dataforcor),2)
write.table(cormatrix, file="Documents/mymatrix.txt", row.names=TRUE, col.names=TRUE)

census.pca <- prcomp(dataforcor[,c(1:36)], center = TRUE, scale. = TRUE)
summary(census.pca)
view(census.pca)


var <- get_pca_var(census.pca)


output <- round(var$contrib,2)
#write.table(output, file="C:/Users/phili/Documents/pcaoutputuk.txt", row.names=TRUE, col.names=TRUE)

pred <- predict(census.pca, newdata=zipcode_data1[,8:47])

#Cluster Zip Codes on 

dataforcluster <- subset(pred, select=c( "PC1",
                                         "PC2", 
                                         "PC3",
                                         "PC4",
                                         "PC5", 
                                         "PC6", "PC7", "PC8", "PC9", "PC10"))


set.seed(25)
zipCluster <- kmeans(dataforcluster[,-c(1)], centers=10, nstart = 25)
cluster_fit <- cbind(dataforcluster, clusterNum = zipCluster$cluster)
head(cluster_fit)

write.table(cluster_fit, file="C:/Users/phili/Documents/coluster_de.txt", row.names=TRUE, col.names=TRUE)

#Merge cluster back to original data
newdata1 <- cbind(zipcode_data1, cluster_fit)
write.table(newdata1, file="UK Clusters.txt", row.names=TRUE, col.names=TRUE)

#test <- subset(PCD_OA_LSOA_MSOA_LAD_AUG19_UK_LU, lsoa11cd=='E01011949')
#rm(test)

###Already set up the code pull from Yelp. ###
London_Manchester_Restos <- read_csv("London Manchester Restos")

uk_resto_zip <- subset(London_Manchester_Restos, select = c(zip_code))
uk_resto_zip <- distinct(uk_resto_zip, zip_code, .keep_all = TRUE)


#Merge UK Postcodes to Zip Codes #
zip_LSOA_key <- merge(uk_resto_zip, PCD_OA_LSOA_MSOA_LAD_AUG19_UK_LU, by.x="zip_code", by.y="pcds")
zip_LSOA_key <- subset(zip_LSOA_key, select = c(zip_code, lsoa11cd))

UK_restos <- merge(London_Manchester_Restos, zip_LSOA_key, by.x = "zip_code", by.y = "zip_code")
UK_restos <- 
  
  
  rm(PCD_OA_LSOA_MSOA_LAD_AUG19_UK_LU)



newdata1a <- subset(newdata1, select = c(LSOA_Code, clusterNum))
UK_restos1 <- merge(UK_restos, newdata1a, by.x="lsoa11cd", by.y="LSOA_Code")

UK_Demographic_Data_Master <- read_excel("UK Demographic Data Master.xlsx")
UK_restos_2 <- merge(UK_restos1, UK_Demographic_Data_Master, by.x="lsoa11cd", by.y="LSOA_Code")
rm(UK_Demographic_Data_Master)

berlin_restos_camden <- subset(berlin_restos1, berlin_restos1$LA_name_2018_boundaries =="Camden")

write.csv(berlin_restos_camden, "Camden restos")
write.csv(berlin_restos1_overview, "London restos by type")


####### Now to Analyze the data ##########
berlin_restos1 <- UK_restos_2
berlin_restos1 <- within(berlin_restos1, dum <- 1)

berlin_restos1_overview <- berlin_restos1 %>%group_by(category_alias, clusterNum) %>%  
  summarize(restos = sum(dum, na.rm = TRUE))

berlin_restos1_overview_type <- berlin_restos1 %>%group_by(category_alias) %>%  
  summarize(restos = sum(dum, na.rm = TRUE))

#write.csv(berlin_restos1_overview_type, "resto type london")

berlin_restos1_overview_type_name <- berlin_restos1 %>%group_by(name, category_title, category_alias, typeaa) %>%  
  summarize(restos = sum(dum, na.rm = TRUE))


#berlin_restos1aa <- berlin_restos1

###Clean up data ###
#berlin_restos1 <- within(berlin_restos1, typeaa <- grepl("Pizza Exp", berlin_restos1$name))
berlin_restos1$category_title <-ifelse(grepl("Pizza Exp", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Pizza Exp", berlin_restos1$name)==TRUE, "pizza", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("McDonal", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("McDonal", berlin_restos1$name)==TRUE, "burgers", berlin_restos1$category_alias)
berlin_restos1$category_title <-ifelse(grepl("Mcdonal", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Mcdonal", berlin_restos1$name)==TRUE, "burgers", berlin_restos1$category_alias)


berlin_restos1$category_title <-ifelse(grepl("KFC", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("KFC", berlin_restos1$name)==TRUE, "chickenshop", berlin_restos1$category_alias)
berlin_restos1$category_title <-ifelse(grepl("Kfc", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Kfc", berlin_restos1$name)==TRUE, "chickenshop", berlin_restos1$category_alias)
berlin_restos1$category_title <-ifelse(grepl("K F C", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("K F C", berlin_restos1$name)==TRUE, "chickenshop", berlin_restos1$category_alias)


berlin_restos1$category_title <-ifelse(grepl("Subway", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Subway", berlin_restos1$name)==TRUE, "sandwiches", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("subway", berlin_restos1$name)==TRUE, "sandwiches", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Pizza Hut", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Pizza Hut", berlin_restos1$name)==TRUE, "pizza", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Nando", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Nando", berlin_restos1$name)==TRUE, "chickenshop", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Domino", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Domino", berlin_restos1$name)==TRUE, "pizza", berlin_restos1$category_alias)
berlin_restos1$category_title <-ifelse(grepl("domino", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("domino", berlin_restos1$name)==TRUE, "pizza", berlin_restos1$category_alias)


berlin_restos1$category_title <-ifelse(grepl("Papa John", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Papa John", berlin_restos1$name)==TRUE, "pizza", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Five Guy", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Five Guy", berlin_restos1$name)==TRUE, "burgers", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Burger King", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Burger King", berlin_restos1$name)==TRUE, "burgers", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Pret A Manger", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Pret A Manger", berlin_restos1$name)==TRUE, "sandwiches", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Pret a Manger", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Pret a Manger", berlin_restos1$name)==TRUE, "sandwiches", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Perfect Fried Chicken", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Perfect Fried Chicken", berlin_restos1$name)==TRUE, "chickenshop", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Chicken Cottage", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Chicken Cottage", berlin_restos1$name)==TRUE, "chickenshop", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Leon", berlin_restos1$name)==TRUE, "Fast Food", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Leon", berlin_restos1$name)==TRUE, "mediterranean", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Caff<e8> Nero", berlin_restos1$name)==TRUE, "Coffee & Tea", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Caff<e8> Nero", berlin_restos1$name)==TRUE, "coffee", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Caffe Nero", berlin_restos1$name)==TRUE, "Coffee & Tea", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Caffe Nero", berlin_restos1$name)==TRUE, "coffee", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Costa", berlin_restos1$name)==TRUE, "Coffee & Tea", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Costa", berlin_restos1$name)==TRUE, "coffee", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Frankie & Benny", berlin_restos1$name)==TRUE, "American (Traditional)", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Frankie & Benny", berlin_restos1$name)==TRUE, "tradamerican", berlin_restos1$category_alias)

#berlin_restos1$category_title <-ifelse(grepl("Fried Chicken", berlin_restos1$name)==TRUE, "American (Traditional)", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Fried Chicken", berlin_restos1$name)==TRUE, "chickenshop", berlin_restos1$category_alias)

berlin_restos1$category_title <-ifelse(grepl("Kebab", berlin_restos1$name)==TRUE, "Kebab", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("Kebab", berlin_restos1$name)==TRUE, "kebab", berlin_restos1$category_alias)
berlin_restos1$category_title <-ifelse(grepl("kebab", berlin_restos1$name)==TRUE, "Kebab", berlin_restos1$category_title)
berlin_restos1$category_alias <-ifelse(grepl("kebab", berlin_restos1$name)==TRUE, "kebab", berlin_restos1$category_alias)

berlin_restos1$category_alias <-ifelse(grepl("Pizza", berlin_restos1$name)==TRUE, "pizza", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("pizza", berlin_restos1$name)==TRUE, "pizza", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Chinese", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Hong Kong", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("China", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Sandwich", berlin_restos1$name)==TRUE, "sandwiches", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Deli", berlin_restos1$name)==TRUE, "sandwiches", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Shanghai", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Thai", berlin_restos1$name)==TRUE, "thai", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse((grepl("Chicken", berlin_restos1$name)==TRUE) & berlin_restos1$category_title=="Fast Food", "chickenshop", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Tandoori", berlin_restos1$name)==TRUE, "indpak", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("India", berlin_restos1$name)==TRUE, "indpak", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Lahore", berlin_restos1$name)==TRUE, "indpak", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Kashmir", berlin_restos1$name)==TRUE, "indpak", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Taj", berlin_restos1$name)==TRUE, "indpak", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Oriental", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Canton", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Peking", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Lotus", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Dragon", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Wok", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Bamboo", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Jade", berlin_restos1$name)==TRUE, "chinese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Japan", berlin_restos1$name)==TRUE, "japanese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse(grepl("Tokyo", berlin_restos1$name)==TRUE, "japanese", berlin_restos1$category_alias)
berlin_restos1$category_alias <-ifelse((grepl("Pizzeria", berlin_restos1$name)==TRUE) & berlin_restos1$category_title=="Fast Food", "pizza", berlin_restos1$category_alias)


#berlin_restos1$category_alias <-ifelse(grepl("Chicken_", berlin_restos1$category_alias)==TRUE, "chickenshop", berlin_restos1$category_alias)
#berlin_restos1$category_alias <-ifelse(grepl("chicken", berlin_restos1$category_alias)==TRUE, "chickenshop", berlin_restos1$category_alias)


berlin_restos1a <- within(berlin_restos1, ifelse(typeaa==TRUE, category_alias=="Pizza", category_alias))
berlin_restos1a <- within(berlin_restos1, ifelse(typeaa==TRUE, category_alias=="Pizza", category_alias))


write.csv(berlin_restos1_overview_zip, "berlin restos1")

library(geosphere)
berlin_restos1 <- subset(berlin_restos1, is.na(latitude) ==FALSE)
berlin_restos1 <- subset(berlin_restos1, is.na(longitude) ==FALSE)
berlin_restos1$lat <- as.numeric(berlin_restos1$latitude)
berlin_restos1$lon <- as.numeric(berlin_restos1$longitude)


berlin_restos1 <- cbind(berlin_restos1, mile_1_all=rowSums(distm (berlin_restos1[,161:162], fun = distHaversine) / 1000 <= 1.6)) # number of points within distance 10000 km
berlin_restos1 <- cbind(berlin_restos1, mile_05_all=rowSums(distm (berlin_restos1[,161:162], fun = distHaversine) / 1000 <= 0.8)) # number of points within distance 10000 km
berlin_restos1 <- cbind(berlin_restos1, mile_025_all=rowSums(distm (berlin_restos1[,161:162], fun = distHaversine) / 1000 <= 0.4)) # number of points within distance 10000 km
berlin_restos1 <- cbind(berlin_restos1, mile_0125_all=rowSums(distm (berlin_restos1[,161:162], fun = distHaversine) / 1000 <= 0.2)) # number of points within distance 10000 km

#berlin_restos_open1 <- merge(berlin_restos_open, plz_5stellig_daten, by.x=c("zip_code"), by.y = c("plz"))
#avg1mile = median(mile_1_all), na.rm = TRUE,
#avg05mile = median(mile_05_all), na.rm = TRUE,
#avg025mile = median(mile_025_all), na.rm = TRUE,
#avg0125mile = median(mile_0125_all), na.rm = TRUE,
#avg1mile_type = median(mile_1_all_type), na.rm = TRUE,
#avg05mile_type = median(mile_05_all_type), na.rm = TRUE,
#avg025mile_type = median(mile_025_all_type), na.rm = TRUE,
#avg0125mile_type = median(mile_0125_all_type), na.rm = TRUE,


berlin_restos2 <- subset(berlin_restos2, `Greater London` =="London")

UK_Demo_cluster <- merge(UK_Demographic_Data_Master, newdata1a, by = "LSOA_Code")

berlin_restos1_overview_zipaa <- UK_Demo_cluster %>%group_by(LSOA_Code, 'MSOA Code', clusterNum) %>%  
  summarize(restos = sum(dum, na.rm = TRUE),
            avgpop = median(Pop, na.rm = TRUE),
            avgdensit = median(`Pop Density`), na.rm = TRUE,
            avginc = median(Income_Rank), na.rm = TRUE,
            avgMed_Age = median( Med_Age), na.rm = TRUE,
            avgpct_AGE_T0004 = median( pct_AGE_T0004), na.rm = TRUE,
            avgpct_AGE_T0509 = median( pct_AGE_T0509), na.rm = TRUE,
            avgpct_AGE_T1014 = median( pct_AGE_T1014), na.rm = TRUE,
            avgpct_AGE_T1519 = median( pct_AGE_T1519), na.rm = TRUE,
            avgpct_AGE_T2024 = median( pct_AGE_T2024), na.rm = TRUE,
            avgpct_AGE_T2529 = median( pct_AGE_T2529), na.rm = TRUE,
            avgpct_AGE_T3034 = median( pct_AGE_T3034), na.rm = TRUE,
            avgpct_AGE_T3539 = median( pct_AGE_T3539), na.rm = TRUE,
            avgpct_AGE_T4044 = median( pct_AGE_T4044), na.rm = TRUE,
            avgpct_AGE_T4549 = median( pct_AGE_T4549), na.rm = TRUE,
            avgpct_AGE_T5054 = median( pct_AGE_T5054), na.rm = TRUE,
            avgpct_AGE_T5559 = median( pct_AGE_T5559), na.rm = TRUE,
            avgpct_AGE_T6064 = median( pct_AGE_T6064), na.rm = TRUE,
            avgpct_AGE_T6569 = median( pct_AGE_T6569), na.rm = TRUE,
            avgpct_AGE_T7074 = median( pct_AGE_T7074), na.rm = TRUE,
            avgpct_AGE_T75PL = median( pct_AGE_T75PL), na.rm = TRUE,
            avgWhite = median( White), na.rm = TRUE,
            avgMixed = median( Mixed), na.rm = TRUE,
            avgAsian = median( Asian), na.rm = TRUE,
            avgAsian_Indian = median( Asian_Indian), na.rm = TRUE,
            avgAsian_Pakistani = median( Asian_Pakistani), na.rm = TRUE,
            avgAsian_Bangladeshi = median( Asian_Bangladeshi), na.rm = TRUE,
            avgAsian_Chinese = median( Asian_Chinese), na.rm = TRUE,
            avgOther_Asian = median( Other_Asian), na.rm = TRUE,
            avgBlack = median( Black), na.rm = TRUE,
            avgBlack_African = median( Black_African), na.rm = TRUE,
            avgBlack_Caribbean = median( Black_Caribbean), na.rm = TRUE,
            avgBlack_Other = median( Black_Other), na.rm = TRUE,
            avgOther = median( Other), na.rm = TRUE,
            avgOther_Arab = median( Other_Arab), na.rm = TRUE,
            avgOther_Other = median( Other_Other), na.rm = TRUE,
            avgIMD_Index = median( IMD_Index), na.rm = TRUE,
            avgIMD_Decile  = median( IMD_Decile ), na.rm = TRUE,
            avgIncome_Rank = median( Income_Rank), na.rm = TRUE,
            avgIncome_Decile = median( Income_Decile), na.rm = TRUE,
            avgForestry = median( `Forestry and logging`), na.rm = TRUE,
            avgFishing = median( `Fishing and aquaculture`), na.rm = TRUE,
            avgCoal = median( `Mining of coal and lignite`), na.rm = TRUE,
            avgOil = median( `Extraction of crude petroleum and natural gas`), na.rm = TRUE,
            avgOre = median( `Mining of metal ores`), na.rm = TRUE,
            avgmining = median( `Other mining and quarrying`), na.rm = TRUE,
            avgMiningSupport = median( `Mining support service activities`), na.rm = TRUE,
            avgFoodMan = median( `Manufacture of food products`), na.rm = TRUE,
            avgBevMan = median( `Manufacture of beverages`), na.rm = TRUE,
            avgTobMan = median( `Manufacture of tobacco products`), na.rm = TRUE,
            avgManTextile = median( `Manufacture of textiles`), na.rm = TRUE,
            avgManApparel = median( `Manufacture of wearing apparel`), na.rm = TRUE,
            avgManLeather = median( `Manufacture of leather and related products`), na.rm = TRUE,
            avgManWood = median( `Manufacture of wood and of products of wood and cork, except furniture;manufacture of articles of straw and plaiting materials`), na.rm = TRUE,
            avgManPaper = median( `Manufacture of paper and paper products`), na.rm = TRUE,
            avgPrinting = median( `Printing and reproduction of recorded media`), na.rm = TRUE,
            avgPetrolMan = median( `Manufacture of coke and refined petroleum products`), na.rm = TRUE,
            avgChemMan = median( `Manufacture of chemicals and chemical products`), na.rm = TRUE,
            avgPharmaMan = median( `Manufacture of basic pharmaceutical products and pharmaceutical preparations`), na.rm = TRUE,
            avgRubberMan = median( `Manufacture of rubber and plastic products`), na.rm = TRUE,
            avgMineralMan = median( `Manufacture of other non-metallic mineral products`), na.rm = TRUE,
            avgManBasicMetal = median( `Manufacture of basic metals`), na.rm = TRUE,
            avgFabMetal = median( `Manufacture of fabricated metal products, except machinery and equipment`), na.rm = TRUE,
            avgManComputers = median( `Manufacture of computer, electronic and optical products`), na.rm = TRUE,
            avgElectricalEquip = median( `Manufacture of electrical equipment`), na.rm = TRUE,
            avgManEquip = median( `Manufacture of machinery and equipment n.e.c.`), na.rm = TRUE,
            avgManCars = median( `Manufacture of motor vehicles, trailers and semi-trailers`), na.rm = TRUE,
            avgManOtherTrans = median( `Manufacture of other transport equipment`), na.rm = TRUE,
            avgFurnMan = median( `Manufacture of furniture`), na.rm = TRUE,
            avgOtherMan= median( `Other manufacturing`), na.rm = TRUE,
            avgRepairMach = median( `Repair and installation of machinery and equipment`), na.rm = TRUE,
            avgElectricity = median( `Electricity, gas, steam and air conditioning supply`), na.rm = TRUE,
            avgWaterTreat = median( `Water collection, treatment and supply`), na.rm = TRUE,
            avgSewer = median( `Sewerage`), na.rm = TRUE,
            avgWasteMgmt = median( `Waste collection, treatment and disposal activities; materials recovery`), na.rm = TRUE,
            avgRemedy = median( `Remediation activities and other waste management services. This division includes the provision of remediation services, i.e. the cleanup of contaminated buildings and sites, soil, surface or ground water.`), na.rm = TRUE,
            avgConstruction = median( `Construction of buildings`), na.rm = TRUE,
            avgCivilEng = median( `Civil engineering`), na.rm = TRUE,
            avgSpecialConst = median( `Specialised construction activities`), na.rm = TRUE,
            avgWholesaleRetail = median( `Wholesale and retail trade and repair of motor vehicles and motorcycles`), na.rm = TRUE,
            avgWholesale = median( `Wholesale trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
            avgRetail = median( `Retail trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
            avgPipeline = median( `Land transport and transport via pipelines`), na.rm = TRUE,
            avgWaterTxp = median( `Water transport`), na.rm = TRUE,
            avgAirTxp = median( `Air transport`), na.rm = TRUE,
            avgWarehouse = median( `Warehousing and support activities for transportation`), na.rm = TRUE,
            avgPost = median( `Postal and courier activities`), na.rm = TRUE,
            avgAccomodation = median( `Accommodation`), na.rm = TRUE,
            avgResto = median( `Food and beverage service activities`), na.rm = TRUE,
            avgPublishing = median( `Publishing activities`), na.rm = TRUE,
            avgMovieProd = median( `Motion picture, video and television programme production, sound recording and music publishing activities`), na.rm = TRUE,
            avgTV = median( `Programming and broadcasting activities`), na.rm = TRUE,
            avgTelecom = median( `Telecommunications`), na.rm = TRUE,
            avgConsult = median( `Computer programming, consultancy and related activities`), na.rm = TRUE,
            avgIT = median( `Information service activities`), na.rm = TRUE,
            avgFinAct = median( `Financial service activities, except insurance and pension funding`), na.rm = TRUE,
            avgInsAct = median( `Insurance, reinsurance and pension funding, except compulsory social security`), na.rm = TRUE,
            avgFinAuxAct = median( `Activities auxiliary to financial services and insurance activities`), na.rm = TRUE,
            avgRealtor = median( `Real estate activities`), na.rm = TRUE,
            avgLegal = median( `Legal and accounting activities`), na.rm = TRUE,
            avgHQ = median( `Activities of head offices; management consultancy activities`), na.rm = TRUE,
            avgArchitect = median( `Architectural and engineering activities; technical testing and analysis`), na.rm = TRUE,
            avgRD = median( `Scientific research and development`), na.rm = TRUE,
            avgMktg = median( `Advertising and market research`), na.rm = TRUE,
            avgProfAct = median( `Other professional, scientific and technical activities`), na.rm = TRUE,
            avgVet = median( `Veterinary activities`), na.rm = TRUE,
            avgRentLease = median( `Rental and leasing activities`), na.rm = TRUE,
            avgEmployAct = median( `Employment activities`), na.rm = TRUE,
            avgTravelTour = median( `Travel agency, tour operator and other reservation service and related activities`), na.rm = TRUE,
            avgSecurity = median( `Security and investigation activities`), na.rm = TRUE,
            avgLandscape = median( `Services to buildings and landscape activities`), na.rm = TRUE,
            avgOffice = median( `Office administrative, office support and other business support activities`), na.rm = TRUE,
            avgPublicAdmin = median( `Public administration and defence; compulsory social security`), na.rm = TRUE,
            avgEducation = median( `Education`), na.rm = TRUE,
            avgHHS = median( `Human health activities`), na.rm = TRUE,
            avgResCare = median( `Residential care activities`), na.rm = TRUE,
            avgSocWork = median( `Social work activities without accommodation`), na.rm = TRUE,
            avgArts = median( `Creative, arts and entertainment activities`), na.rm = TRUE,
            avgLibraries = median( `Libraries, archives, museums and other cultural activities`), na.rm = TRUE,
            avgCasino = median( `Gambling and betting activities`), na.rm = TRUE,
            avgSportsAct= median( `Sports activities and amusement and recreation activities`), na.rm = TRUE,
            avgClubs = median( `Activities of membership organisations`), na.rm = TRUE,
            avgRepairHH = median( `Repair of computers and personal and household goods`), na.rm = TRUE,
            avgOther = median( `Other personal service activities`), na.rm = TRUE,
            avgDomesticHelp = median( `Activities of households as employers of domestic personnel`), na.rm = TRUE,
            avgUndifHH = median( `Undifferentiated goods- and services-producing activities of private households for own use`), na.rm = TRUE,
            avgETs = median( `Activities of extraterritorial organisations and bodies`), na.rm = TRUE)

cluster_data_melted <- melt(berlin_restos1_overview_zipaa, id=1:3)



write.csv(berlin_restos1_overview_zipaa, file="london msoa", row.names=TRUE, col.names=TRUE)


berlin_restos1_overview_zipabc <- UK_Demo_cluster %>%group_by(clusterNum) %>%  
  summarize(restos = sum(dum, na.rm = TRUE),
            avgpop = median(Pop, na.rm = TRUE),
            avgdensit = median(`Pop Density`), na.rm = TRUE,
            avginc = median(Income_Rank), na.rm = TRUE,
            avgMed_Age = median( Med_Age), na.rm = TRUE,
            avgpct_AGE_T0004 = median( pct_AGE_T0004), na.rm = TRUE,
            avgpct_AGE_T0509 = median( pct_AGE_T0509), na.rm = TRUE,
            avgpct_AGE_T1014 = median( pct_AGE_T1014), na.rm = TRUE,
            avgpct_AGE_T1519 = median( pct_AGE_T1519), na.rm = TRUE,
            avgpct_AGE_T2024 = median( pct_AGE_T2024), na.rm = TRUE,
            avgpct_AGE_T2529 = median( pct_AGE_T2529), na.rm = TRUE,
            avgpct_AGE_T3034 = median( pct_AGE_T3034), na.rm = TRUE,
            avgpct_AGE_T3539 = median( pct_AGE_T3539), na.rm = TRUE,
            avgpct_AGE_T4044 = median( pct_AGE_T4044), na.rm = TRUE,
            avgpct_AGE_T4549 = median( pct_AGE_T4549), na.rm = TRUE,
            avgpct_AGE_T5054 = median( pct_AGE_T5054), na.rm = TRUE,
            avgpct_AGE_T5559 = median( pct_AGE_T5559), na.rm = TRUE,
            avgpct_AGE_T6064 = median( pct_AGE_T6064), na.rm = TRUE,
            avgpct_AGE_T6569 = median( pct_AGE_T6569), na.rm = TRUE,
            avgpct_AGE_T7074 = median( pct_AGE_T7074), na.rm = TRUE,
            avgpct_AGE_T75PL = median( pct_AGE_T75PL), na.rm = TRUE,
            avgWhite = median( White), na.rm = TRUE,
            avgMixed = median( Mixed), na.rm = TRUE,
            avgAsian = median( Asian), na.rm = TRUE,
            avgAsian_Indian = median( Asian_Indian), na.rm = TRUE,
            avgAsian_Pakistani = median( Asian_Pakistani), na.rm = TRUE,
            avgAsian_Bangladeshi = median( Asian_Bangladeshi), na.rm = TRUE,
            avgAsian_Chinese = median( Asian_Chinese), na.rm = TRUE,
            avgOther_Asian = median( Other_Asian), na.rm = TRUE,
            avgBlack = median( Black), na.rm = TRUE,
            avgBlack_African = median( Black_African), na.rm = TRUE,
            avgBlack_Caribbean = median( Black_Caribbean), na.rm = TRUE,
            avgBlack_Other = median( Black_Other), na.rm = TRUE,
            avgOther = median( Other), na.rm = TRUE,
            avgOther_Arab = median( Other_Arab), na.rm = TRUE,
            avgOther_Other = median( Other_Other), na.rm = TRUE,
            avgIMD_Index = median( IMD_Index), na.rm = TRUE,
            avgIMD_Decile  = median( IMD_Decile ), na.rm = TRUE,
            avgIncome_Rank = median( Income_Rank), na.rm = TRUE,
            avgIncome_Decile = median( Income_Decile), na.rm = TRUE,
            avgForestry = median( `Forestry and logging`), na.rm = TRUE,
            avgFishing = median( `Fishing and aquaculture`), na.rm = TRUE,
            avgCoal = median( `Mining of coal and lignite`), na.rm = TRUE,
            avgOil = median( `Extraction of crude petroleum and natural gas`), na.rm = TRUE,
            avgOre = median( `Mining of metal ores`), na.rm = TRUE,
            avgmining = median( `Other mining and quarrying`), na.rm = TRUE,
            avgMiningSupport = median( `Mining support service activities`), na.rm = TRUE,
            avgFoodMan = median( `Manufacture of food products`), na.rm = TRUE,
            avgBevMan = median( `Manufacture of beverages`), na.rm = TRUE,
            avgTobMan = median( `Manufacture of tobacco products`), na.rm = TRUE,
            avgManTextile = median( `Manufacture of textiles`), na.rm = TRUE,
            avgManApparel = median( `Manufacture of wearing apparel`), na.rm = TRUE,
            avgManLeather = median( `Manufacture of leather and related products`), na.rm = TRUE,
            avgManWood = median( `Manufacture of wood and of products of wood and cork, except furniture;manufacture of articles of straw and plaiting materials`), na.rm = TRUE,
            avgManPaper = median( `Manufacture of paper and paper products`), na.rm = TRUE,
            avgPrinting = median( `Printing and reproduction of recorded media`), na.rm = TRUE,
            avgPetrolMan = median( `Manufacture of coke and refined petroleum products`), na.rm = TRUE,
            avgChemMan = median( `Manufacture of chemicals and chemical products`), na.rm = TRUE,
            avgPharmaMan = median( `Manufacture of basic pharmaceutical products and pharmaceutical preparations`), na.rm = TRUE,
            avgRubberMan = median( `Manufacture of rubber and plastic products`), na.rm = TRUE,
            avgMineralMan = median( `Manufacture of other non-metallic mineral products`), na.rm = TRUE,
            avgManBasicMetal = median( `Manufacture of basic metals`), na.rm = TRUE,
            avgFabMetal = median( `Manufacture of fabricated metal products, except machinery and equipment`), na.rm = TRUE,
            avgManComputers = median( `Manufacture of computer, electronic and optical products`), na.rm = TRUE,
            avgElectricalEquip = median( `Manufacture of electrical equipment`), na.rm = TRUE,
            avgManEquip = median( `Manufacture of machinery and equipment n.e.c.`), na.rm = TRUE,
            avgManCars = median( `Manufacture of motor vehicles, trailers and semi-trailers`), na.rm = TRUE,
            avgManOtherTrans = median( `Manufacture of other transport equipment`), na.rm = TRUE,
            avgFurnMan = median( `Manufacture of furniture`), na.rm = TRUE,
            avgOtherMan= median( `Other manufacturing`), na.rm = TRUE,
            avgRepairMach = median( `Repair and installation of machinery and equipment`), na.rm = TRUE,
            avgElectricity = median( `Electricity, gas, steam and air conditioning supply`), na.rm = TRUE,
            avgWaterTreat = median( `Water collection, treatment and supply`), na.rm = TRUE,
            avgSewer = median( `Sewerage`), na.rm = TRUE,
            avgWasteMgmt = median( `Waste collection, treatment and disposal activities; materials recovery`), na.rm = TRUE,
            avgRemedy = median( `Remediation activities and other waste management services. This division includes the provision of remediation services, i.e. the cleanup of contaminated buildings and sites, soil, surface or ground water.`), na.rm = TRUE,
            avgConstruction = median( `Construction of buildings`), na.rm = TRUE,
            avgCivilEng = median( `Civil engineering`), na.rm = TRUE,
            avgSpecialConst = median( `Specialised construction activities`), na.rm = TRUE,
            avgWholesaleRetail = median( `Wholesale and retail trade and repair of motor vehicles and motorcycles`), na.rm = TRUE,
            avgWholesale = median( `Wholesale trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
            avgRetail = median( `Retail trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
            avgPipeline = median( `Land transport and transport via pipelines`), na.rm = TRUE,
            avgWaterTxp = median( `Water transport`), na.rm = TRUE,
            avgAirTxp = median( `Air transport`), na.rm = TRUE,
            avgWarehouse = median( `Warehousing and support activities for transportation`), na.rm = TRUE,
            avgPost = median( `Postal and courier activities`), na.rm = TRUE,
            avgAccomodation = median( `Accommodation`), na.rm = TRUE,
            avgResto = median( `Food and beverage service activities`), na.rm = TRUE,
            avgPublishing = median( `Publishing activities`), na.rm = TRUE,
            avgMovieProd = median( `Motion picture, video and television programme production, sound recording and music publishing activities`), na.rm = TRUE,
            avgTV = median( `Programming and broadcasting activities`), na.rm = TRUE,
            avgTelecom = median( `Telecommunications`), na.rm = TRUE,
            avgConsult = median( `Computer programming, consultancy and related activities`), na.rm = TRUE,
            avgIT = median( `Information service activities`), na.rm = TRUE,
            avgFinAct = median( `Financial service activities, except insurance and pension funding`), na.rm = TRUE,
            avgInsAct = median( `Insurance, reinsurance and pension funding, except compulsory social security`), na.rm = TRUE,
            avgFinAuxAct = median( `Activities auxiliary to financial services and insurance activities`), na.rm = TRUE,
            avgRealtor = median( `Real estate activities`), na.rm = TRUE,
            avgLegal = median( `Legal and accounting activities`), na.rm = TRUE,
            avgHQ = median( `Activities of head offices; management consultancy activities`), na.rm = TRUE,
            avgArchitect = median( `Architectural and engineering activities; technical testing and analysis`), na.rm = TRUE,
            avgRD = median( `Scientific research and development`), na.rm = TRUE,
            avgMktg = median( `Advertising and market research`), na.rm = TRUE,
            avgProfAct = median( `Other professional, scientific and technical activities`), na.rm = TRUE,
            avgVet = median( `Veterinary activities`), na.rm = TRUE,
            avgRentLease = median( `Rental and leasing activities`), na.rm = TRUE,
            avgEmployAct = median( `Employment activities`), na.rm = TRUE,
            avgTravelTour = median( `Travel agency, tour operator and other reservation service and related activities`), na.rm = TRUE,
            avgSecurity = median( `Security and investigation activities`), na.rm = TRUE,
            avgLandscape = median( `Services to buildings and landscape activities`), na.rm = TRUE,
            avgOffice = median( `Office administrative, office support and other business support activities`), na.rm = TRUE,
            avgPublicAdmin = median( `Public administration and defence; compulsory social security`), na.rm = TRUE,
            avgEducation = median( `Education`), na.rm = TRUE,
            avgHHS = median( `Human health activities`), na.rm = TRUE,
            avgResCare = median( `Residential care activities`), na.rm = TRUE,
            avgSocWork = median( `Social work activities without accommodation`), na.rm = TRUE,
            avgArts = median( `Creative, arts and entertainment activities`), na.rm = TRUE,
            avgLibraries = median( `Libraries, archives, museums and other cultural activities`), na.rm = TRUE,
            avgCasino = median( `Gambling and betting activities`), na.rm = TRUE,
            avgSportsAct= median( `Sports activities and amusement and recreation activities`), na.rm = TRUE,
            avgClubs = median( `Activities of membership organisations`), na.rm = TRUE,
            avgRepairHH = median( `Repair of computers and personal and household goods`), na.rm = TRUE,
            avgOther = median( `Other personal service activities`), na.rm = TRUE,
            avgDomesticHelp = median( `Activities of households as employers of domestic personnel`), na.rm = TRUE,
            avgUndifHH = median( `Undifferentiated goods- and services-producing activities of private households for own use`), na.rm = TRUE,
            avgETs = median( `Activities of extraterritorial organisations and bodies`), na.rm = TRUE)

cluster_avg_data_melted <- melt(berlin_restos1_overview_zipabc, id=1)







#avg1mile = median(mile_1_all), na.rm = TRUE,
#avg05mile = median(mile_05_all), na.rm = TRUE,
#avg025mile = median(mile_025_all), na.rm = TRUE,
#avg0125mile = median(mile_0125_all), na.rm = TRUE,
#avg1mile_type = median(mile_1_all_type), na.rm = TRUE,
#avg05mile_type = median(mile_05_all_type), na.rm = TRUE,
#avg025mile_type = median(mile_025_all_type), na.rm = TRUE,
#avg0125mile_type = median(mile_0125_all_type), na.rm = TRUE,

berlin_restos1_overview_zipab <- berlin_restos2 %>%group_by(clusterNum) %>%  
  summarize(restos = sum(dum, na.rm = TRUE),
            avgpop = median(Pop, na.rm = TRUE),
            avgdensit = median(`Pop Density`), na.rm = TRUE,
            avginc = median(Income_Rank), na.rm = TRUE,
            avgMed_Age = median( Med_Age), na.rm = TRUE,
            avgpct_AGE_T0004 = median( pct_AGE_T0004), na.rm = TRUE,
            avgpct_AGE_T0509 = median( pct_AGE_T0509), na.rm = TRUE,
            avgpct_AGE_T1014 = median( pct_AGE_T1014), na.rm = TRUE,
            avgpct_AGE_T1519 = median( pct_AGE_T1519), na.rm = TRUE,
            avgpct_AGE_T2024 = median( pct_AGE_T2024), na.rm = TRUE,
            avgpct_AGE_T2529 = median( pct_AGE_T2529), na.rm = TRUE,
            avgpct_AGE_T3034 = median( pct_AGE_T3034), na.rm = TRUE,
            avgpct_AGE_T3539 = median( pct_AGE_T3539), na.rm = TRUE,
            avgpct_AGE_T4044 = median( pct_AGE_T4044), na.rm = TRUE,
            avgpct_AGE_T4549 = median( pct_AGE_T4549), na.rm = TRUE,
            avgpct_AGE_T5054 = median( pct_AGE_T5054), na.rm = TRUE,
            avgpct_AGE_T5559 = median( pct_AGE_T5559), na.rm = TRUE,
            avgpct_AGE_T6064 = median( pct_AGE_T6064), na.rm = TRUE,
            avgpct_AGE_T6569 = median( pct_AGE_T6569), na.rm = TRUE,
            avgpct_AGE_T7074 = median( pct_AGE_T7074), na.rm = TRUE,
            avgpct_AGE_T75PL = median( pct_AGE_T75PL), na.rm = TRUE,
            avgWhite = median( White), na.rm = TRUE,
            avgMixed = median( Mixed), na.rm = TRUE,
            avgAsian = median( Asian), na.rm = TRUE,
            avgAsian_Indian = median( Asian_Indian), na.rm = TRUE,
            avgAsian_Pakistani = median( Asian_Pakistani), na.rm = TRUE,
            avgAsian_Bangladeshi = median( Asian_Bangladeshi), na.rm = TRUE,
            avgAsian_Chinese = median( Asian_Chinese), na.rm = TRUE,
            avgOther_Asian = median( Other_Asian), na.rm = TRUE,
            avgBlack = median( Black), na.rm = TRUE,
            avgBlack_African = median( Black_African), na.rm = TRUE,
            avgBlack_Caribbean = median( Black_Caribbean), na.rm = TRUE,
            avgBlack_Other = median( Black_Other), na.rm = TRUE,
            avgOther = median( Other), na.rm = TRUE,
            avgOther_Arab = median( Other_Arab), na.rm = TRUE,
            avgOther_Other = median( Other_Other), na.rm = TRUE,
            avgIMD_Index = median( IMD_Index), na.rm = TRUE,
            avgIMD_Decile  = median( IMD_Decile ), na.rm = TRUE,
            avgIncome_Rank = median( Income_Rank), na.rm = TRUE,
            avgIncome_Decile = median( Income_Decile), na.rm = TRUE,
            avgForestry = median( `Forestry and logging`), na.rm = TRUE,
            avgFishing = median( `Fishing and aquaculture`), na.rm = TRUE,
            avgCoal = median( `Mining of coal and lignite`), na.rm = TRUE,
            avgOil = median( `Extraction of crude petroleum and natural gas`), na.rm = TRUE,
            avgOre = median( `Mining of metal ores`), na.rm = TRUE,
            avgmining = median( `Other mining and quarrying`), na.rm = TRUE,
            avgMiningSupport = median( `Mining support service activities`), na.rm = TRUE,
            avgFoodMan = median( `Manufacture of food products`), na.rm = TRUE,
            avgBevMan = median( `Manufacture of beverages`), na.rm = TRUE,
            avgTobMan = median( `Manufacture of tobacco products`), na.rm = TRUE,
            avgManTextile = median( `Manufacture of textiles`), na.rm = TRUE,
            avgManApparel = median( `Manufacture of wearing apparel`), na.rm = TRUE,
            avgManLeather = median( `Manufacture of leather and related products`), na.rm = TRUE,
            avgManWood = median( `Manufacture of wood and of products of wood and cork, except furniture;manufacture of articles of straw and plaiting materials`), na.rm = TRUE,
            avgManPaper = median( `Manufacture of paper and paper products`), na.rm = TRUE,
            avgPrinting = median( `Printing and reproduction of recorded media`), na.rm = TRUE,
            avgPetrolMan = median( `Manufacture of coke and refined petroleum products`), na.rm = TRUE,
            avgChemMan = median( `Manufacture of chemicals and chemical products`), na.rm = TRUE,
            avgPharmaMan = median( `Manufacture of basic pharmaceutical products and pharmaceutical preparations`), na.rm = TRUE,
            avgRubberMan = median( `Manufacture of rubber and plastic products`), na.rm = TRUE,
            avgMineralMan = median( `Manufacture of other non-metallic mineral products`), na.rm = TRUE,
            avgManBasicMetal = median( `Manufacture of basic metals`), na.rm = TRUE,
            avgFabMetal = median( `Manufacture of fabricated metal products, except machinery and equipment`), na.rm = TRUE,
            avgManComputers = median( `Manufacture of computer, electronic and optical products`), na.rm = TRUE,
            avgElectricalEquip = median( `Manufacture of electrical equipment`), na.rm = TRUE,
            avgManEquip = median( `Manufacture of machinery and equipment n.e.c.`), na.rm = TRUE,
            avgManCars = median( `Manufacture of motor vehicles, trailers and semi-trailers`), na.rm = TRUE,
            avgManOtherTrans = median( `Manufacture of other transport equipment`), na.rm = TRUE,
            avgFurnMan = median( `Manufacture of furniture`), na.rm = TRUE,
            avgOtherMan= median( `Other manufacturing`), na.rm = TRUE,
            avgRepairMach = median( `Repair and installation of machinery and equipment`), na.rm = TRUE,
            avgElectricity = median( `Electricity, gas, steam and air conditioning supply`), na.rm = TRUE,
            avgWaterTreat = median( `Water collection, treatment and supply`), na.rm = TRUE,
            avgSewer = median( `Sewerage`), na.rm = TRUE,
            avgWasteMgmt = median( `Waste collection, treatment and disposal activities; materials recovery`), na.rm = TRUE,
            avgRemedy = median( `Remediation activities and other waste management services. This division includes the provision of remediation services, i.e. the cleanup of contaminated buildings and sites, soil, surface or ground water.`), na.rm = TRUE,
            avgConstruction = median( `Construction of buildings`), na.rm = TRUE,
            avgCivilEng = median( `Civil engineering`), na.rm = TRUE,
            avgSpecialConst = median( `Specialised construction activities`), na.rm = TRUE,
            avgWholesaleRetail = median( `Wholesale and retail trade and repair of motor vehicles and motorcycles`), na.rm = TRUE,
            avgWholesale = median( `Wholesale trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
            avgRetail = median( `Retail trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
            avgPipeline = median( `Land transport and transport via pipelines`), na.rm = TRUE,
            avgWaterTxp = median( `Water transport`), na.rm = TRUE,
            avgAirTxp = median( `Air transport`), na.rm = TRUE,
            avgWarehouse = median( `Warehousing and support activities for transportation`), na.rm = TRUE,
            avgPost = median( `Postal and courier activities`), na.rm = TRUE,
            avgAccomodation = median( `Accommodation`), na.rm = TRUE,
            avgResto = median( `Food and beverage service activities`), na.rm = TRUE,
            avgPublishing = median( `Publishing activities`), na.rm = TRUE,
            avgMovieProd = median( `Motion picture, video and television programme production, sound recording and music publishing activities`), na.rm = TRUE,
            avgTV = median( `Programming and broadcasting activities`), na.rm = TRUE,
            avgTelecom = median( `Telecommunications`), na.rm = TRUE,
            avgConsult = median( `Computer programming, consultancy and related activities`), na.rm = TRUE,
            avgIT = median( `Information service activities`), na.rm = TRUE,
            avgFinAct = median( `Financial service activities, except insurance and pension funding`), na.rm = TRUE,
            avgInsAct = median( `Insurance, reinsurance and pension funding, except compulsory social security`), na.rm = TRUE,
            avgFinAuxAct = median( `Activities auxiliary to financial services and insurance activities`), na.rm = TRUE,
            avgRealtor = median( `Real estate activities`), na.rm = TRUE,
            avgLegal = median( `Legal and accounting activities`), na.rm = TRUE,
            avgHQ = median( `Activities of head offices; management consultancy activities`), na.rm = TRUE,
            avgArchitect = median( `Architectural and engineering activities; technical testing and analysis`), na.rm = TRUE,
            avgRD = median( `Scientific research and development`), na.rm = TRUE,
            avgMktg = median( `Advertising and market research`), na.rm = TRUE,
            avgProfAct = median( `Other professional, scientific and technical activities`), na.rm = TRUE,
            avgVet = median( `Veterinary activities`), na.rm = TRUE,
            avgRentLease = median( `Rental and leasing activities`), na.rm = TRUE,
            avgEmployAct = median( `Employment activities`), na.rm = TRUE,
            avgTravelTour = median( `Travel agency, tour operator and other reservation service and related activities`), na.rm = TRUE,
            avgSecurity = median( `Security and investigation activities`), na.rm = TRUE,
            avgLandscape = median( `Services to buildings and landscape activities`), na.rm = TRUE,
            avgOffice = median( `Office administrative, office support and other business support activities`), na.rm = TRUE,
            avgPublicAdmin = median( `Public administration and defence; compulsory social security`), na.rm = TRUE,
            avgEducation = median( `Education`), na.rm = TRUE,
            avgHHS = median( `Human health activities`), na.rm = TRUE,
            avgResCare = median( `Residential care activities`), na.rm = TRUE,
            avgSocWork = median( `Social work activities without accommodation`), na.rm = TRUE,
            avgArts = median( `Creative, arts and entertainment activities`), na.rm = TRUE,
            avgLibraries = median( `Libraries, archives, museums and other cultural activities`), na.rm = TRUE,
            avgCasino = median( `Gambling and betting activities`), na.rm = TRUE,
            avgSportsAct= median( `Sports activities and amusement and recreation activities`), na.rm = TRUE,
            avgClubs = median( `Activities of membership organisations`), na.rm = TRUE,
            avgRepairHH = median( `Repair of computers and personal and household goods`), na.rm = TRUE,
            avgOther = median( `Other personal service activities`), na.rm = TRUE,
            avgDomesticHelp = median( `Activities of households as employers of domestic personnel`), na.rm = TRUE,
            avgUndifHH = median( `Undifferentiated goods- and services-producing activities of private households for own use`), na.rm = TRUE,
            avgETs = median( `Activities of extraterritorial organisations and bodies`), na.rm = TRUE)

#coravg1mile=cor(restos,avg1mile), 
#coravg05mile=cor(restos,avg05mile), 
#coravg025mile=cor(restos,avg025mile), 
#coravg0125mile=cor(restos,avg0125mile), 
#coravg1mile_type=cor(restos,avg1mile_type), 
#coravg05mile_type=cor(restos,avg05mile_type), 
#coravg025mile_type=cor(restos,avg025mile_type), 
#coravg0125mile_type=cor(restos,avg0125mile_type), 

corr_by_cluster <- berlin_restos1_overview_zipab %>% group_by(clusterNum) %>%
  summarize(coravgpop=cor(restos,avgpop), 
            coravgdensit=cor(restos,avgdensit), 
            coravginc=cor(restos,avginc), 
            coravgMed_Age=cor(restos,avgMed_Age), 
            coravgpct_AGE_T0004=cor(restos,avgpct_AGE_T0004), 
            coravgpct_AGE_T0509=cor(restos,avgpct_AGE_T0509), 
            coravgpct_AGE_T1014=cor(restos,avgpct_AGE_T1014), 
            coravgpct_AGE_T1519=cor(restos,avgpct_AGE_T1519), 
            coravgpct_AGE_T2024=cor(restos,avgpct_AGE_T2024), 
            coravgpct_AGE_T2529=cor(restos,avgpct_AGE_T2529), 
            coravgpct_AGE_T3034=cor(restos,avgpct_AGE_T3034), 
            coravgpct_AGE_T3539=cor(restos,avgpct_AGE_T3539), 
            coravgpct_AGE_T4044=cor(restos,avgpct_AGE_T4044), 
            coravgpct_AGE_T4549=cor(restos,avgpct_AGE_T4549), 
            coravgpct_AGE_T5054=cor(restos,avgpct_AGE_T5054), 
            coravgpct_AGE_T5559=cor(restos,avgpct_AGE_T5559), 
            coravgpct_AGE_T6064=cor(restos,avgpct_AGE_T6064), 
            coravgpct_AGE_T6569=cor(restos,avgpct_AGE_T6569), 
            coravgpct_AGE_T7074=cor(restos,avgpct_AGE_T7074), 
            coravgpct_AGE_T75PL=cor(restos,avgpct_AGE_T75PL), 
            coravgWhite=cor(restos,avgWhite), 
            coravgMixed=cor(restos,avgMixed), 
            coravgAsian=cor(restos,avgAsian), 
            coravgAsian_Indian=cor(restos,avgAsian_Indian), 
            coravgAsian_Pakistani=cor(restos,avgAsian_Pakistani), 
            coravgAsian_Bangladeshi=cor(restos,avgAsian_Bangladeshi), 
            coravgAsian_Chinese=cor(restos,avgAsian_Chinese), 
            coravgOther_Asian=cor(restos,avgOther_Asian), 
            coravgBlack=cor(restos,avgBlack), 
            coravgBlack_African=cor(restos,avgBlack_African), 
            coravgBlack_Caribbean=cor(restos,avgBlack_Caribbean), 
            coravgBlack_Other=cor(restos,avgBlack_Other), 
            coravgOther=cor(restos,avgOther), 
            coravgOther_Arab=cor(restos,avgOther_Arab), 
            coravgOther_Other=cor(restos,avgOther_Other), 
            coravgIMD_Index=cor(restos,avgIMD_Index), 
            coravgIMD_Decile=cor(restos,avgIMD_Decile), 
            coravgIncome_Rank=cor(restos,avgIncome_Rank), 
            coravgIncome_Decile=cor(restos,avgIncome_Decile), 
            coravgForestry=cor(restos,avgForestry), 
            coravgFishing=cor(restos,avgFishing), 
            coravgCoal=cor(restos,avgCoal), 
            coravgOil=cor(restos,avgOil), 
            coravgOre=cor(restos,avgOre), 
            coravgmining=cor(restos,avgmining), 
            coravgMiningSupport=cor(restos,avgMiningSupport), 
            coravgFoodMan=cor(restos,avgFoodMan), 
            coravgBevMan=cor(restos,avgBevMan), 
            coravgTobMan=cor(restos,avgTobMan), 
            coravgManTextile=cor(restos,avgManTextile), 
            coravgManApparel=cor(restos,avgManApparel), 
            coravgManLeather=cor(restos,avgManLeather), 
            coravgManWood=cor(restos,avgManWood), 
            coravgManPaper=cor(restos,avgManPaper), 
            coravgPrinting=cor(restos,avgPrinting), 
            coravgPetrolMan=cor(restos,avgPetrolMan), 
            coravgChemMan=cor(restos,avgChemMan), 
            coravgPharmaMan=cor(restos,avgPharmaMan), 
            coravgRubberMan=cor(restos,avgRubberMan), 
            coravgMineralMan=cor(restos,avgMineralMan), 
            coravgManBasicMetal=cor(restos,avgManBasicMetal), 
            coravgFabMetal=cor(restos,avgFabMetal), 
            coravgManComputers=cor(restos,avgManComputers), 
            coravgElectricalEquip=cor(restos,avgElectricalEquip), 
            coravgManEquip=cor(restos,avgManEquip), 
            coravgManCars=cor(restos,avgManCars), 
            coravgManOtherTrans=cor(restos,avgManOtherTrans), 
            coravgFurnMan=cor(restos,avgFurnMan), 
            coravgOtherMan=cor(restos,avgOtherMan), 
            coravgRepairMach=cor(restos,avgRepairMach), 
            coravgElectricity=cor(restos,avgElectricity), 
            coravgWaterTreat=cor(restos,avgWaterTreat), 
            coravgSewer=cor(restos,avgSewer), 
            coravgWasteMgmt=cor(restos,avgWasteMgmt), 
            coravgRemedy=cor(restos,avgRemedy), 
            coravgConstruction=cor(restos,avgConstruction), 
            coravgCivilEng=cor(restos,avgCivilEng), 
            coravgSpecialConst=cor(restos,avgSpecialConst), 
            coravgWholesaleRetail=cor(restos,avgWholesaleRetail), 
            coravgWholesale=cor(restos,avgWholesale), 
            coravgRetail=cor(restos,avgRetail), 
            coravgPipeline=cor(restos,avgPipeline), 
            coravgWaterTxp=cor(restos,avgWaterTxp), 
            coravgAirTxp=cor(restos,avgAirTxp), 
            coravgWarehouse=cor(restos,avgWarehouse), 
            coravgPost=cor(restos,avgPost), 
            coravgAccomodation=cor(restos,avgAccomodation), 
            coravgResto=cor(restos,avgResto), 
            coravgPublishing=cor(restos,avgPublishing), 
            coravgMovieProd=cor(restos,avgMovieProd), 
            coravgTV=cor(restos,avgTV), 
            coravgTelecom=cor(restos,avgTelecom), 
            coravgConsult=cor(restos,avgConsult), 
            coravgIT=cor(restos,avgIT), 
            coravgFinAct=cor(restos,avgFinAct), 
            coravgInsAct=cor(restos,avgInsAct), 
            coravgFinAuxAct=cor(restos,avgFinAuxAct), 
            coravgRealtor=cor(restos,avgRealtor), 
            coravgLegal=cor(restos,avgLegal), 
            coravgHQ=cor(restos,avgHQ), 
            coravgArchitect=cor(restos,avgArchitect), 
            coravgRD=cor(restos,avgRD), 
            coravgMktg=cor(restos,avgMktg), 
            coravgProfAct=cor(restos,avgProfAct), 
            coravgVet=cor(restos,avgVet), 
            coravgRentLease=cor(restos,avgRentLease), 
            coravgEmployAct=cor(restos,avgEmployAct), 
            coravgTravelTour=cor(restos,avgTravelTour), 
            coravgSecurity=cor(restos,avgSecurity), 
            coravgLandscape=cor(restos,avgLandscape), 
            coravgOffice=cor(restos,avgOffice), 
            coravgPublicAdmin=cor(restos,avgPublicAdmin), 
            coravgEducation=cor(restos,avgEducation), 
            coravgHHS=cor(restos,avgHHS), 
            coravgResCare=cor(restos,avgResCare), 
            coravgSocWork=cor(restos,avgSocWork), 
            coravgArts=cor(restos,avgArts), 
            coravgLibraries=cor(restos,avgLibraries), 
            coravgCasino=cor(restos,avgCasino), 
            coravgSportsAct=cor(restos,avgSportsAct), 
            coravgClubs=cor(restos,avgClubs), 
            coravgRepairHH=cor(restos,avgRepairHH), 
            coravgOther=cor(restos,avgOther), 
            coravgDomesticHelp=cor(restos,avgDomesticHelp), 
            coravgUndifHH=cor(restos,avgUndifHH), 
            coravgETs=cor(restos,avgETs))

corr_by_cluster_melted <- melt(corr_by_cluster, id=1)
corr_by_cluster_melted <- rename(corr_by_cluster_melted, correlation = value)
corr_by_cluster_melted <- within(corr_by_cluster_melted, variable <- substr(variable, 4,30))

rankings<- corr_by_cluster_melted %>%
  group_by(clusterNum) %>%
  mutate(good_ranks = order(order(abs(correlation), decreasing=TRUE)))


msoa_data_eval_1 <- merge(cluster_data_melted, rankings, by = c("clusterNum", "variable"))

#avg1mile = median(mile_1_all), na.rm = TRUE,
#avg05mile = median(mile_05_all), na.rm = TRUE,
#avg025mile = median(mile_025_all), na.rm = TRUE,
#avg0125mile = median(mile_0125_all), na.rm = TRUE,
#avg1mile_type = median(mile_1_all_type), na.rm = TRUE,
#avg05mile_type = median(mile_05_all_type), na.rm = TRUE,
#avg025mile_type = median(mile_025_all_type), na.rm = TRUE,
#avg0125mile_type = median(mile_0125_all_type), na.rm = TRUE,

berlin_restos1_overview_zipaa_cluster <- UK_Demo_cluster %>%group_by(clusterNum) %>%  
  summarize(restos = sum(dum, na.rm = TRUE),
            avgpop = median(Pop, na.rm = TRUE),
            avgdensit = median(`Pop Density`), na.rm = TRUE,
            avginc = median(Income_Rank), na.rm = TRUE,
            avgMed_Age = median( Med_Age), na.rm = TRUE,
            avgpct_AGE_T0004 = median( pct_AGE_T0004), na.rm = TRUE,
            avgpct_AGE_T0509 = median( pct_AGE_T0509), na.rm = TRUE,
            avgpct_AGE_T1014 = median( pct_AGE_T1014), na.rm = TRUE,
            avgpct_AGE_T1519 = median( pct_AGE_T1519), na.rm = TRUE,
            avgpct_AGE_T2024 = median( pct_AGE_T2024), na.rm = TRUE,
            avgpct_AGE_T2529 = median( pct_AGE_T2529), na.rm = TRUE,
            avgpct_AGE_T3034 = median( pct_AGE_T3034), na.rm = TRUE,
            avgpct_AGE_T3539 = median( pct_AGE_T3539), na.rm = TRUE,
            avgpct_AGE_T4044 = median( pct_AGE_T4044), na.rm = TRUE,
            avgpct_AGE_T4549 = median( pct_AGE_T4549), na.rm = TRUE,
            avgpct_AGE_T5054 = median( pct_AGE_T5054), na.rm = TRUE,
            avgpct_AGE_T5559 = median( pct_AGE_T5559), na.rm = TRUE,
            avgpct_AGE_T6064 = median( pct_AGE_T6064), na.rm = TRUE,
            avgpct_AGE_T6569 = median( pct_AGE_T6569), na.rm = TRUE,
            avgpct_AGE_T7074 = median( pct_AGE_T7074), na.rm = TRUE,
            avgpct_AGE_T75PL = median( pct_AGE_T75PL), na.rm = TRUE,
            avgWhite = median( White), na.rm = TRUE,
            avgMixed = median( Mixed), na.rm = TRUE,
            avgAsian = median( Asian), na.rm = TRUE,
            avgAsian_Indian = median( Asian_Indian), na.rm = TRUE,
            avgAsian_Pakistani = median( Asian_Pakistani), na.rm = TRUE,
            avgAsian_Bangladeshi = median( Asian_Bangladeshi), na.rm = TRUE,
            avgAsian_Chinese = median( Asian_Chinese), na.rm = TRUE,
            avgOther_Asian = median( Other_Asian), na.rm = TRUE,
            avgBlack = median( Black), na.rm = TRUE,
            avgBlack_African = median( Black_African), na.rm = TRUE,
            avgBlack_Caribbean = median( Black_Caribbean), na.rm = TRUE,
            avgBlack_Other = median( Black_Other), na.rm = TRUE,
            avgOther = median( Other), na.rm = TRUE,
            avgOther_Arab = median( Other_Arab), na.rm = TRUE,
            avgOther_Other = median( Other_Other), na.rm = TRUE,
            avgIMD_Index = median( IMD_Index), na.rm = TRUE,
            avgIMD_Decile  = median( IMD_Decile ), na.rm = TRUE,
            avgIncome_Rank = median( Income_Rank), na.rm = TRUE,
            avgIncome_Decile = median( Income_Decile), na.rm = TRUE,
            avgForestry = median( `Forestry and logging`), na.rm = TRUE,
            avgFishing = median( `Fishing and aquaculture`), na.rm = TRUE,
            avgCoal = median( `Mining of coal and lignite`), na.rm = TRUE,
            avgOil = median( `Extraction of crude petroleum and natural gas`), na.rm = TRUE,
            avgOre = median( `Mining of metal ores`), na.rm = TRUE,
            avgmining = median( `Other mining and quarrying`), na.rm = TRUE,
            avgMiningSupport = median( `Mining support service activities`), na.rm = TRUE,
            avgFoodMan = median( `Manufacture of food products`), na.rm = TRUE,
            avgBevMan = median( `Manufacture of beverages`), na.rm = TRUE,
            avgTobMan = median( `Manufacture of tobacco products`), na.rm = TRUE,
            avgManTextile = median( `Manufacture of textiles`), na.rm = TRUE,
            avgManApparel = median( `Manufacture of wearing apparel`), na.rm = TRUE,
            avgManLeather = median( `Manufacture of leather and related products`), na.rm = TRUE,
            avgManWood = median( `Manufacture of wood and of products of wood and cork, except furniture;manufacture of articles of straw and plaiting materials`), na.rm = TRUE,
            avgManPaper = median( `Manufacture of paper and paper products`), na.rm = TRUE,
            avgPrinting = median( `Printing and reproduction of recorded media`), na.rm = TRUE,
            avgPetrolMan = median( `Manufacture of coke and refined petroleum products`), na.rm = TRUE,
            avgChemMan = median( `Manufacture of chemicals and chemical products`), na.rm = TRUE,
            avgPharmaMan = median( `Manufacture of basic pharmaceutical products and pharmaceutical preparations`), na.rm = TRUE,
            avgRubberMan = median( `Manufacture of rubber and plastic products`), na.rm = TRUE,
            avgMineralMan = median( `Manufacture of other non-metallic mineral products`), na.rm = TRUE,
            avgManBasicMetal = median( `Manufacture of basic metals`), na.rm = TRUE,
            avgFabMetal = median( `Manufacture of fabricated metal products, except machinery and equipment`), na.rm = TRUE,
            avgManComputers = median( `Manufacture of computer, electronic and optical products`), na.rm = TRUE,
            avgElectricalEquip = median( `Manufacture of electrical equipment`), na.rm = TRUE,
            avgManEquip = median( `Manufacture of machinery and equipment n.e.c.`), na.rm = TRUE,
            avgManCars = median( `Manufacture of motor vehicles, trailers and semi-trailers`), na.rm = TRUE,
            avgManOtherTrans = median( `Manufacture of other transport equipment`), na.rm = TRUE,
            avgFurnMan = median( `Manufacture of furniture`), na.rm = TRUE,
            avgOtherMan= median( `Other manufacturing`), na.rm = TRUE,
            avgRepairMach = median( `Repair and installation of machinery and equipment`), na.rm = TRUE,
            avgElectricity = median( `Electricity, gas, steam and air conditioning supply`), na.rm = TRUE,
            avgWaterTreat = median( `Water collection, treatment and supply`), na.rm = TRUE,
            avgSewer = median( `Sewerage`), na.rm = TRUE,
            avgWasteMgmt = median( `Waste collection, treatment and disposal activities; materials recovery`), na.rm = TRUE,
            avgRemedy = median( `Remediation activities and other waste management services. This division includes the provision of remediation services, i.e. the cleanup of contaminated buildings and sites, soil, surface or ground water.`), na.rm = TRUE,
            avgConstruction = median( `Construction of buildings`), na.rm = TRUE,
            avgCivilEng = median( `Civil engineering`), na.rm = TRUE,
            avgSpecialConst = median( `Specialised construction activities`), na.rm = TRUE,
            avgWholesaleRetail = median( `Wholesale and retail trade and repair of motor vehicles and motorcycles`), na.rm = TRUE,
            avgWholesale = median( `Wholesale trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
            avgRetail = median( `Retail trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
            avgPipeline = median( `Land transport and transport via pipelines`), na.rm = TRUE,
            avgWaterTxp = median( `Water transport`), na.rm = TRUE,
            avgAirTxp = median( `Air transport`), na.rm = TRUE,
            avgWarehouse = median( `Warehousing and support activities for transportation`), na.rm = TRUE,
            avgPost = median( `Postal and courier activities`), na.rm = TRUE,
            avgAccomodation = median( `Accommodation`), na.rm = TRUE,
            avgResto = median( `Food and beverage service activities`), na.rm = TRUE,
            avgPublishing = median( `Publishing activities`), na.rm = TRUE,
            avgMovieProd = median( `Motion picture, video and television programme production, sound recording and music publishing activities`), na.rm = TRUE,
            avgTV = median( `Programming and broadcasting activities`), na.rm = TRUE,
            avgTelecom = median( `Telecommunications`), na.rm = TRUE,
            avgConsult = median( `Computer programming, consultancy and related activities`), na.rm = TRUE,
            avgIT = median( `Information service activities`), na.rm = TRUE,
            avgFinAct = median( `Financial service activities, except insurance and pension funding`), na.rm = TRUE,
            avgInsAct = median( `Insurance, reinsurance and pension funding, except compulsory social security`), na.rm = TRUE,
            avgFinAuxAct = median( `Activities auxiliary to financial services and insurance activities`), na.rm = TRUE,
            avgRealtor = median( `Real estate activities`), na.rm = TRUE,
            avgLegal = median( `Legal and accounting activities`), na.rm = TRUE,
            avgHQ = median( `Activities of head offices; management consultancy activities`), na.rm = TRUE,
            avgArchitect = median( `Architectural and engineering activities; technical testing and analysis`), na.rm = TRUE,
            avgRD = median( `Scientific research and development`), na.rm = TRUE,
            avgMktg = median( `Advertising and market research`), na.rm = TRUE,
            avgProfAct = median( `Other professional, scientific and technical activities`), na.rm = TRUE,
            avgVet = median( `Veterinary activities`), na.rm = TRUE,
            avgRentLease = median( `Rental and leasing activities`), na.rm = TRUE,
            avgEmployAct = median( `Employment activities`), na.rm = TRUE,
            avgTravelTour = median( `Travel agency, tour operator and other reservation service and related activities`), na.rm = TRUE,
            avgSecurity = median( `Security and investigation activities`), na.rm = TRUE,
            avgLandscape = median( `Services to buildings and landscape activities`), na.rm = TRUE,
            avgOffice = median( `Office administrative, office support and other business support activities`), na.rm = TRUE,
            avgPublicAdmin = median( `Public administration and defence; compulsory social security`), na.rm = TRUE,
            avgEducation = median( `Education`), na.rm = TRUE,
            avgHHS = median( `Human health activities`), na.rm = TRUE,
            avgResCare = median( `Residential care activities`), na.rm = TRUE,
            avgSocWork = median( `Social work activities without accommodation`), na.rm = TRUE,
            avgArts = median( `Creative, arts and entertainment activities`), na.rm = TRUE,
            avgLibraries = median( `Libraries, archives, museums and other cultural activities`), na.rm = TRUE,
            avgCasino = median( `Gambling and betting activities`), na.rm = TRUE,
            avgSportsAct= median( `Sports activities and amusement and recreation activities`), na.rm = TRUE,
            avgClubs = median( `Activities of membership organisations`), na.rm = TRUE,
            avgRepairHH = median( `Repair of computers and personal and household goods`), na.rm = TRUE,
            avgOther = median( `Other personal service activities`), na.rm = TRUE,
            avgDomesticHelp = median( `Activities of households as employers of domestic personnel`), na.rm = TRUE,
            avgUndifHH = median( `Undifferentiated goods- and services-producing activities of private households for own use`), na.rm = TRUE,
            avgETs = median( `Activities of extraterritorial organisations and bodies`), na.rm = TRUE)

clust_avg_data_melted <- melt(berlin_restos1_overview_zipaa_cluster, id=1)
clust_avg_data_melted <- rename(clust_avg_data_melted, avg = value)

msoa_eval_data <- merge(msoa_data_eval_1, clust_avg_data_melted, by = c("clusterNum", "variable"))

msoa_eval_data <- within(msoa_eval_data, factordif <- (value - avg)*correlation)
msoa_eval_data <- subset(msoa_eval_data, good_ranks < 20)


msoa_eval_data1 <- msoa_eval_data %>%group_by(clusterNum, LSOA_Code) %>%  
  summarize(score = sum(factordif, na.rm = TRUE))

msoa_min <- min(msoa_eval_data1$score)

msoa_eval_data2 <- merge(msoa_eval_data1, msoa_min)
msoa_eval_data2 <- within(msoa_eval_data2, revised_score <- score-y)

msoa_max <- max(msoa_eval_data2$revised_score)
msoa_eval_data2 <- subset(msoa_eval_data2, select=-c(y))

msoa_eval_data3 <- merge(msoa_eval_data2, msoa_max)
msoa_eval_data3 <- within(msoa_eval_data3, normalized_score <- 100*(revised_score/y))

msoa_data <- subset(UK_Demographic_Data_Master, select=c(LSOA_Code, LSOA_Name))
msoa_data <- unique.data.frame(msoa_data)

msoa_eval_data4 <- merge(msoa_eval_data3, msoa_data, by.x =("LSOA_Code") , by.y =c("LSOA_Code"))

msoa_eval_data5 <- msoa_eval_data4 %>%  mutate(good_ranks = order(order(abs(score), decreasing=TRUE)))


berlin_restos1_overview_type_price <- berlin_restos1 %>%group_by(category_alias, price) %>%  
  summarize(restos = sum(dum, na.rm = TRUE))

#berlin_restos1 <- within(berlin_restos1, typeaa <- grepl("Noodles", berlin_restos1$name))

berlin_restos1_overview_type_price1 <- subset(berlin_restos1_overview_type_price, restos>=50)
berlin_restos1_overview_type_price1 <- subset(berlin_restos1_overview_type_price1, price != "NA")


berlin_restos1_overview_type <- berlin_restos1 %>%group_by(category_alias) %>%  
  summarize(restos = sum(dum, na.rm = TRUE))

berlin_restos1_overview_type1 <- subset(berlin_restos1_overview_type, restos>=50)
rm(msoa_data_eval_final)

berlin_restos1_overview_price <- berlin_restos1 %>%group_by(price) %>%  
  summarize(restos = sum(dum, na.rm = TRUE))

#####Doing this by resto type #####
for(i in 1:nrow(berlin_restos1_overview_type1))
{  
  berlin_restos1_type <- subset(berlin_restos1,  (category_alias == berlin_restos1_overview_type1$category_alias[i]))
  
  resto_types <- subset(berlin_restos1_type, select = c(category_alias))
  resto_types <- resto_types[!duplicated(resto_types$category_alias), ]
  
  # berlin_restos1_type <- cbind(berlin_restos1_type, mile_1_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 1.6)) # number of points within distance 10000 km
  #  berlin_restos1_type <- cbind(berlin_restos1_type, mile_05_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.8)) # number of points within distance 10000 km
  #  berlin_restos1_type <- cbind(berlin_restos1_type, mile_025_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.4)) # number of points within distance 10000 km
  #  berlin_restos1_type <- cbind(berlin_restos1_type, mile_0125_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.2)) # number of points within distance 10000 km
  
  # berlin_restos1_type <- within(berlin_restos1_type, mile_1_all_type <- mile_1_all_type-1)
  #  berlin_restos1_type <- within(berlin_restos1_type, mile_05_all_type <- mile_05_all_type-1)
  #  berlin_restos1_type <- within(berlin_restos1_type, mile_025_all_type <- mile_025_all_type-1)
  #  berlin_restos1_type <- within(berlin_restos1_type, mile_0125_all_type <- mile_0125_all_type-1)
  
  # berlin_restos1_type1 <- subset(berlin_restos1_type, select = c(id, mile_1_all_type, mile_05_all_type, mile_025_all_type, mile_0125_all_type))
  
  #  berlin_restos2 <- merge(berlin_restos1, berlin_restos1_type1, by.x = "id", by.y = "id", all.x = TRUE)
  #  berlin_retstos2 <- subset(berlin_restos2, is.na(id)==FALSE)
  
  #write.csv(berlin_restos1_type, "berlin restos1 type")
  
  
  
  #  cluster_type_data_melted <- melt(berlin_restos1_overview_zipaa_type, id=1:3)
  
  
  #write.csv(berlin_restos1_overview_zipaa_type, "berlin restos1 type overview")
  #coravg1mile=cor(restos,avg1mile), 
  #coravg05mile=cor(restos,avg05mile), 
  #coravg025mile=cor(restos,avg025mile), 
  #coravg0125mile=cor(restos,avg0125mile), 
  #coravg1mile_type=cor(restos,avg1mile_type), 
  #coravg05mile_type=cor(restos,avg05mile_type), 
  #coravg025mile_type=cor(restos,avg025mile_type), 
  #coravg0125mile_type=cor(restos,avg0125mile_type), 
  #  avg1mile = median(mile_1_all), na.rm = TRUE,
  # avg05mile = median(mile_05_all), na.rm = TRUE,
  #avg025mile = median(mile_025_all), na.rm = TRUE,
  #avg0125mile = median(mile_0125_all), na.rm = TRUE,
  #avg1mile_type = median(mile_1_all_type), na.rm = TRUE,
  #avg05mile_type = median(mile_05_all_type), na.rm = TRUE,
  #avg025mile_type = median(mile_025_all_type), na.rm = TRUE,
  #avg0125mile_type = median(mile_0125_all_type), na.rm = TRUE,
  
  berlin_restos1_overview_zipaa_type <- berlin_restos1_type %>% group_by(`Greater London`, lsoa11cd, clusterNum) %>%  
    summarize(restos = sum(dum, na.rm = TRUE),
              avgpop = median(Pop, na.rm = TRUE),
              avgdensit = median(`Pop Density`), na.rm = TRUE,
              avginc = median(Income_Rank), na.rm = TRUE,
              avgMed_Age = median(Med_Age), na.rm = TRUE,
              avgpct_AGE_T0004 = median( pct_AGE_T0004), na.rm = TRUE,
              avgpct_AGE_T0509 = median( pct_AGE_T0509), na.rm = TRUE,
              avgpct_AGE_T1014 = median( pct_AGE_T1014), na.rm = TRUE,
              avgpct_AGE_T1519 = median( pct_AGE_T1519), na.rm = TRUE,
              avgpct_AGE_T2024 = median( pct_AGE_T2024), na.rm = TRUE,
              avgpct_AGE_T2529 = median( pct_AGE_T2529), na.rm = TRUE,
              avgpct_AGE_T3034 = median( pct_AGE_T3034), na.rm = TRUE,
              avgpct_AGE_T3539 = median( pct_AGE_T3539), na.rm = TRUE,
              avgpct_AGE_T4044 = median( pct_AGE_T4044), na.rm = TRUE,
              avgpct_AGE_T4549 = median( pct_AGE_T4549), na.rm = TRUE,
              avgpct_AGE_T5054 = median( pct_AGE_T5054), na.rm = TRUE,
              avgpct_AGE_T5559 = median( pct_AGE_T5559), na.rm = TRUE,
              avgpct_AGE_T6064 = median( pct_AGE_T6064), na.rm = TRUE,
              avgpct_AGE_T6569 = median( pct_AGE_T6569), na.rm = TRUE,
              avgpct_AGE_T7074 = median( pct_AGE_T7074), na.rm = TRUE,
              avgpct_AGE_T75PL = median( pct_AGE_T75PL), na.rm = TRUE,
              avgWhite = median( White), na.rm = TRUE,
              avgMixed = median( Mixed), na.rm = TRUE,
              avgAsian = median( Asian), na.rm = TRUE,
              avgAsian_Indian = median( Asian_Indian), na.rm = TRUE,
              avgAsian_Pakistani = median( Asian_Pakistani), na.rm = TRUE,
              avgAsian_Bangladeshi = median( Asian_Bangladeshi), na.rm = TRUE,
              avgAsian_Chinese = median( Asian_Chinese), na.rm = TRUE,
              avgOther_Asian = median( Other_Asian), na.rm = TRUE,
              avgBlack = median( Black), na.rm = TRUE,
              avgBlack_African = median( Black_African), na.rm = TRUE,
              avgBlack_Caribbean = median( Black_Caribbean), na.rm = TRUE,
              avgBlack_Other = median( Black_Other), na.rm = TRUE,
              avgOther = median( Other), na.rm = TRUE,
              avgOther_Arab = median( Other_Arab), na.rm = TRUE,
              avgOther_Other = median( Other_Other), na.rm = TRUE,
              avgIMD_Index = median( IMD_Index), na.rm = TRUE,
              avgIMD_Decile  = median( IMD_Decile ), na.rm = TRUE,
              avgIncome_Rank = median( Income_Rank), na.rm = TRUE,
              avgIncome_Decile = median( Income_Decile), na.rm = TRUE,
              avgForestry = median( `Forestry and logging`), na.rm = TRUE,
              avgFishing = median( `Fishing and aquaculture`), na.rm = TRUE,
              avgCoal = median( `Mining of coal and lignite`), na.rm = TRUE,
              avgOil = median( `Extraction of crude petroleum and natural gas`), na.rm = TRUE,
              avgOre = median( `Mining of metal ores`), na.rm = TRUE,
              avgmining = median( `Other mining and quarrying`), na.rm = TRUE,
              avgMiningSupport = median( `Mining support service activities`), na.rm = TRUE,
              avgFoodMan = median( `Manufacture of food products`), na.rm = TRUE,
              avgBevMan = median( `Manufacture of beverages`), na.rm = TRUE,
              avgTobMan = median( `Manufacture of tobacco products`), na.rm = TRUE,
              avgManTextile = median( `Manufacture of textiles`), na.rm = TRUE,
              avgManApparel = median( `Manufacture of wearing apparel`), na.rm = TRUE,
              avgManLeather = median( `Manufacture of leather and related products`), na.rm = TRUE,
              avgManWood = median( `Manufacture of wood and of products of wood and cork, except furniture;manufacture of articles of straw and plaiting materials`), na.rm = TRUE,
              avgManPaper = median( `Manufacture of paper and paper products`), na.rm = TRUE,
              avgPrinting = median( `Printing and reproduction of recorded media`), na.rm = TRUE,
              avgPetrolMan = median( `Manufacture of coke and refined petroleum products`), na.rm = TRUE,
              avgChemMan = median( `Manufacture of chemicals and chemical products`), na.rm = TRUE,
              avgPharmaMan = median( `Manufacture of basic pharmaceutical products and pharmaceutical preparations`), na.rm = TRUE,
              avgRubberMan = median( `Manufacture of rubber and plastic products`), na.rm = TRUE,
              avgMineralMan = median( `Manufacture of other non-metallic mineral products`), na.rm = TRUE,
              avgManBasicMetal = median( `Manufacture of basic metals`), na.rm = TRUE,
              avgFabMetal = median( `Manufacture of fabricated metal products, except machinery and equipment`), na.rm = TRUE,
              avgManComputers = median( `Manufacture of computer, electronic and optical products`), na.rm = TRUE,
              avgElectricalEquip = median( `Manufacture of electrical equipment`), na.rm = TRUE,
              avgManEquip = median( `Manufacture of machinery and equipment n.e.c.`), na.rm = TRUE,
              avgManCars = median( `Manufacture of motor vehicles, trailers and semi-trailers`), na.rm = TRUE,
              avgManOtherTrans = median( `Manufacture of other transport equipment`), na.rm = TRUE,
              avgFurnMan = median( `Manufacture of furniture`), na.rm = TRUE,
              avgOtherMan= median( `Other manufacturing`), na.rm = TRUE,
              avgRepairMach = median( `Repair and installation of machinery and equipment`), na.rm = TRUE,
              avgElectricity = median( `Electricity, gas, steam and air conditioning supply`), na.rm = TRUE,
              avgWaterTreat = median( `Water collection, treatment and supply`), na.rm = TRUE,
              avgSewer = median( `Sewerage`), na.rm = TRUE,
              avgWasteMgmt = median( `Waste collection, treatment and disposal activities; materials recovery`), na.rm = TRUE,
              avgRemedy = median( `Remediation activities and other waste management services. This division includes the provision of remediation services, i.e. the cleanup of contaminated buildings and sites, soil, surface or ground water.`), na.rm = TRUE,
              avgConstruction = median( `Construction of buildings`), na.rm = TRUE,
              avgCivilEng = median( `Civil engineering`), na.rm = TRUE,
              avgSpecialConst = median( `Specialised construction activities`), na.rm = TRUE,
              avgWholesaleRetail = median( `Wholesale and retail trade and repair of motor vehicles and motorcycles`), na.rm = TRUE,
              avgWholesale = median( `Wholesale trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
              avgRetail = median( `Retail trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
              avgPipeline = median( `Land transport and transport via pipelines`), na.rm = TRUE,
              avgWaterTxp = median( `Water transport`), na.rm = TRUE,
              avgAirTxp = median( `Air transport`), na.rm = TRUE,
              avgWarehouse = median( `Warehousing and support activities for transportation`), na.rm = TRUE,
              avgPost = median( `Postal and courier activities`), na.rm = TRUE,
              avgAccomodation = median( `Accommodation`), na.rm = TRUE,
              avgResto = median( `Food and beverage service activities`), na.rm = TRUE,
              avgPublishing = median( `Publishing activities`), na.rm = TRUE,
              avgMovieProd = median( `Motion picture, video and television programme production, sound recording and music publishing activities`), na.rm = TRUE,
              avgTV = median( `Programming and broadcasting activities`), na.rm = TRUE,
              avgTelecom = median( `Telecommunications`), na.rm = TRUE,
              avgConsult = median( `Computer programming, consultancy and related activities`), na.rm = TRUE,
              avgIT = median( `Information service activities`), na.rm = TRUE,
              avgFinAct = median( `Financial service activities, except insurance and pension funding`), na.rm = TRUE,
              avgInsAct = median( `Insurance, reinsurance and pension funding, except compulsory social security`), na.rm = TRUE,
              avgFinAuxAct = median( `Activities auxiliary to financial services and insurance activities`), na.rm = TRUE,
              avgRealtor = median( `Real estate activities`), na.rm = TRUE,
              avgLegal = median( `Legal and accounting activities`), na.rm = TRUE,
              avgHQ = median( `Activities of head offices; management consultancy activities`), na.rm = TRUE,
              avgArchitect = median( `Architectural and engineering activities; technical testing and analysis`), na.rm = TRUE,
              avgRD = median( `Scientific research and development`), na.rm = TRUE,
              avgMktg = median( `Advertising and market research`), na.rm = TRUE,
              avgProfAct = median( `Other professional, scientific and technical activities`), na.rm = TRUE,
              avgVet = median( `Veterinary activities`), na.rm = TRUE,
              avgRentLease = median( `Rental and leasing activities`), na.rm = TRUE,
              avgEmployAct = median( `Employment activities`), na.rm = TRUE,
              avgTravelTour = median( `Travel agency, tour operator and other reservation service and related activities`), na.rm = TRUE,
              avgSecurity = median( `Security and investigation activities`), na.rm = TRUE,
              avgLandscape = median( `Services to buildings and landscape activities`), na.rm = TRUE,
              avgOffice = median( `Office administrative, office support and other business support activities`), na.rm = TRUE,
              avgPublicAdmin = median( `Public administration and defence; compulsory social security`), na.rm = TRUE,
              avgEducation = median( `Education`), na.rm = TRUE,
              avgHHS = median( `Human health activities`), na.rm = TRUE,
              avgResCare = median( `Residential care activities`), na.rm = TRUE,
              avgSocWork = median( `Social work activities without accommodation`), na.rm = TRUE,
              avgArts = median( `Creative, arts and entertainment activities`), na.rm = TRUE,
              avgLibraries = median( `Libraries, archives, museums and other cultural activities`), na.rm = TRUE,
              avgCasino = median( `Gambling and betting activities`), na.rm = TRUE,
              avgSportsAct= median( `Sports activities and amusement and recreation activities`), na.rm = TRUE,
              avgClubs = median( `Activities of membership organisations`), na.rm = TRUE,
              avgRepairHH = median( `Repair of computers and personal and household goods`), na.rm = TRUE,
              avgOther = median( `Other personal service activities`), na.rm = TRUE,
              avgDomesticHelp = median( `Activities of households as employers of domestic personnel`), na.rm = TRUE,
              avgUndifHH = median( `Undifferentiated goods- and services-producing activities of private households for own use`), na.rm = TRUE,
              avgETs = median( `Activities of extraterritorial organisations and bodies`), na.rm = TRUE)
  
  corr_by_cluster_type <- berlin_restos1_overview_zipaa_type %>% group_by(clusterNum) %>%
    summarize(coravgpop=cor(restos,avgpop), 
              coravgdensit=cor(restos,avgdensit), 
              coravginc=cor(restos,avginc), 
              coravgMed_Age=cor(restos,avgMed_Age), 
              
              coravgpct_AGE_T0004=cor(restos,avgpct_AGE_T0004), 
              coravgpct_AGE_T0509=cor(restos,avgpct_AGE_T0509), 
              coravgpct_AGE_T1014=cor(restos,avgpct_AGE_T1014), 
              coravgpct_AGE_T1519=cor(restos,avgpct_AGE_T1519), 
              coravgpct_AGE_T2024=cor(restos,avgpct_AGE_T2024), 
              coravgpct_AGE_T2529=cor(restos,avgpct_AGE_T2529), 
              coravgpct_AGE_T3034=cor(restos,avgpct_AGE_T3034), 
              coravgpct_AGE_T3539=cor(restos,avgpct_AGE_T3539), 
              coravgpct_AGE_T4044=cor(restos,avgpct_AGE_T4044), 
              coravgpct_AGE_T4549=cor(restos,avgpct_AGE_T4549), 
              coravgpct_AGE_T5054=cor(restos,avgpct_AGE_T5054), 
              coravgpct_AGE_T5559=cor(restos,avgpct_AGE_T5559), 
              coravgpct_AGE_T6064=cor(restos,avgpct_AGE_T6064), 
              coravgpct_AGE_T6569=cor(restos,avgpct_AGE_T6569), 
              coravgpct_AGE_T7074=cor(restos,avgpct_AGE_T7074), 
              coravgpct_AGE_T75PL=cor(restos,avgpct_AGE_T75PL), 
              coravgWhite=cor(restos,avgWhite), 
              coravgMixed=cor(restos,avgMixed), 
              coravgAsian=cor(restos,avgAsian), 
              coravgAsian_Indian=cor(restos,avgAsian_Indian), 
              coravgAsian_Pakistani=cor(restos,avgAsian_Pakistani), 
              coravgAsian_Bangladeshi=cor(restos,avgAsian_Bangladeshi), 
              coravgAsian_Chinese=cor(restos,avgAsian_Chinese), 
              coravgOther_Asian=cor(restos,avgOther_Asian), 
              coravgBlack=cor(restos,avgBlack), 
              coravgBlack_African=cor(restos,avgBlack_African), 
              coravgBlack_Caribbean=cor(restos,avgBlack_Caribbean), 
              coravgBlack_Other=cor(restos,avgBlack_Other), 
              coravgOther=cor(restos,avgOther), 
              coravgOther_Arab=cor(restos,avgOther_Arab), 
              coravgOther_Other=cor(restos,avgOther_Other), 
              coravgIMD_Index=cor(restos,avgIMD_Index), 
              coravgIMD_Decile=cor(restos,avgIMD_Decile), 
              coravgIncome_Rank=cor(restos,avgIncome_Rank), 
              coravgIncome_Decile=cor(restos,avgIncome_Decile), 
              coravgForestry=cor(restos,avgForestry), 
              coravgFishing=cor(restos,avgFishing), 
              coravgCoal=cor(restos,avgCoal), 
              coravgOil=cor(restos,avgOil), 
              coravgOre=cor(restos,avgOre), 
              coravgmining=cor(restos,avgmining), 
              coravgMiningSupport=cor(restos,avgMiningSupport), 
              coravgFoodMan=cor(restos,avgFoodMan), 
              coravgBevMan=cor(restos,avgBevMan), 
              coravgTobMan=cor(restos,avgTobMan), 
              coravgManTextile=cor(restos,avgManTextile), 
              coravgManApparel=cor(restos,avgManApparel), 
              coravgManLeather=cor(restos,avgManLeather), 
              coravgManWood=cor(restos,avgManWood), 
              coravgManPaper=cor(restos,avgManPaper), 
              coravgPrinting=cor(restos,avgPrinting), 
              coravgPetrolMan=cor(restos,avgPetrolMan), 
              coravgChemMan=cor(restos,avgChemMan), 
              coravgPharmaMan=cor(restos,avgPharmaMan), 
              coravgRubberMan=cor(restos,avgRubberMan), 
              coravgMineralMan=cor(restos,avgMineralMan), 
              coravgManBasicMetal=cor(restos,avgManBasicMetal), 
              coravgFabMetal=cor(restos,avgFabMetal), 
              coravgManComputers=cor(restos,avgManComputers), 
              coravgElectricalEquip=cor(restos,avgElectricalEquip), 
              coravgManEquip=cor(restos,avgManEquip), 
              coravgManCars=cor(restos,avgManCars), 
              coravgManOtherTrans=cor(restos,avgManOtherTrans), 
              coravgFurnMan=cor(restos,avgFurnMan), 
              coravgOtherMan=cor(restos,avgOtherMan), 
              coravgRepairMach=cor(restos,avgRepairMach), 
              coravgElectricity=cor(restos,avgElectricity), 
              coravgWaterTreat=cor(restos,avgWaterTreat), 
              coravgSewer=cor(restos,avgSewer), 
              coravgWasteMgmt=cor(restos,avgWasteMgmt), 
              coravgRemedy=cor(restos,avgRemedy), 
              coravgConstruction=cor(restos,avgConstruction), 
              coravgCivilEng=cor(restos,avgCivilEng), 
              coravgSpecialConst=cor(restos,avgSpecialConst), 
              coravgWholesaleRetail=cor(restos,avgWholesaleRetail), 
              coravgWholesale=cor(restos,avgWholesale), 
              coravgRetail=cor(restos,avgRetail), 
              coravgPipeline=cor(restos,avgPipeline), 
              coravgWaterTxp=cor(restos,avgWaterTxp), 
              coravgAirTxp=cor(restos,avgAirTxp), 
              coravgWarehouse=cor(restos,avgWarehouse), 
              coravgPost=cor(restos,avgPost), 
              coravgAccomodation=cor(restos,avgAccomodation), 
              coravgResto=cor(restos,avgResto), 
              coravgPublishing=cor(restos,avgPublishing), 
              coravgMovieProd=cor(restos,avgMovieProd), 
              coravgTV=cor(restos,avgTV), 
              coravgTelecom=cor(restos,avgTelecom), 
              coravgConsult=cor(restos,avgConsult), 
              coravgIT=cor(restos,avgIT), 
              coravgFinAct=cor(restos,avgFinAct), 
              coravgInsAct=cor(restos,avgInsAct), 
              coravgFinAuxAct=cor(restos,avgFinAuxAct), 
              coravgRealtor=cor(restos,avgRealtor), 
              coravgLegal=cor(restos,avgLegal), 
              coravgHQ=cor(restos,avgHQ), 
              coravgArchitect=cor(restos,avgArchitect), 
              coravgRD=cor(restos,avgRD), 
              coravgMktg=cor(restos,avgMktg), 
              coravgProfAct=cor(restos,avgProfAct), 
              coravgVet=cor(restos,avgVet), 
              coravgRentLease=cor(restos,avgRentLease), 
              coravgEmployAct=cor(restos,avgEmployAct), 
              coravgTravelTour=cor(restos,avgTravelTour), 
              coravgSecurity=cor(restos,avgSecurity), 
              coravgLandscape=cor(restos,avgLandscape), 
              coravgOffice=cor(restos,avgOffice), 
              coravgPublicAdmin=cor(restos,avgPublicAdmin), 
              coravgEducation=cor(restos,avgEducation), 
              coravgHHS=cor(restos,avgHHS), 
              coravgResCare=cor(restos,avgResCare), 
              coravgSocWork=cor(restos,avgSocWork), 
              coravgArts=cor(restos,avgArts), 
              coravgLibraries=cor(restos,avgLibraries), 
              coravgCasino=cor(restos,avgCasino), 
              coravgSportsAct=cor(restos,avgSportsAct), 
              coravgClubs=cor(restos,avgClubs), 
              coravgRepairHH=cor(restos,avgRepairHH), 
              coravgOther=cor(restos,avgOther), 
              coravgDomesticHelp=cor(restos,avgDomesticHelp), 
              coravgUndifHH=cor(restos,avgUndifHH), 
              coravgETs=cor(restos,avgETs))
  
  
  corr_by_cluster_type_melted <- melt(corr_by_cluster_type, id=1)
  corr_by_cluster_type_melted <- rename(corr_by_cluster_type_melted, correlation = value)
  corr_by_cluster_type_melted <- within(corr_by_cluster_type_melted, variable <- substr(variable, 4,30))
  
  rankings_type<- corr_by_cluster_type_melted %>%
    group_by(clusterNum) %>%
    mutate(good_ranks = order(order(abs(correlation), decreasing=TRUE)))
  
  
  msoa_data_eval_type_1 <- merge(cluster_data_melted, rankings_type, by = c("clusterNum", "variable"))
  
  
  msoa_data_eval_type <- merge(msoa_data_eval_type_1, cluster_avg_data_melted, by = c("clusterNum", "variable"))
  
  msoa_data_eval_type <- subset(msoa_data_eval_type, is.na(correlation)==FALSE)
  
  msoa_data_eval_type <- subset(msoa_data_eval_type, is.na(correlation)==FALSE)
  msoa_data_eval_type <- msoa_data_eval_type %>% rename(value = value.x)
  msoa_data_eval_type <- msoa_data_eval_type %>% rename(avg = value.y)
  
  msoa_data_eval_type <- within(msoa_data_eval_type, factordif <- (value - avg)*correlation)
  #msoa_eval_data_type <- subset(msoa_eval_data_type, good_ranks < 20)
  
  
  msoa_eval_data_type1 <-   msoa_data_eval_type %>%group_by(clusterNum, LSOA_Code) %>%  
    summarize(score = sum(factordif, na.rm = TRUE))
  
  msoa_min_type <- min(msoa_eval_data_type1$score)
  
  msoa_eval_data_type2 <- merge(msoa_eval_data_type1, msoa_min_type)
  msoa_eval_data_type2 <- within(msoa_eval_data_type2, revised_score <- score-y)
  
  msoa_max_type <- max(msoa_eval_data_type2$revised_score)
  msoa_eval_data_type2 <- subset(msoa_eval_data_type2, select=-c(y))
  
  msoa_eval_data_type3 <- merge(msoa_eval_data_type2, msoa_max_type)
  msoa_eval_data_type3 <- within(msoa_eval_data_type3, normalized_score <- 100*(revised_score/y))
  
  msoa_data <- subset(UK_Demographic_Data_Master, select=c(LSOA_Code, LSOA_Name))
  msoa_data <- unique.data.frame(msoa_data)
  
  msoa_eval_data_type4 <- merge(msoa_eval_data_type3, msoa_data, by.x = ("LSOA_Code"), by.y = c("LSOA_Code"))
  
  msoa_eval_data_type5 <- msoa_eval_data_type4 %>%  mutate(good_ranks = order(order(abs(score), decreasing=TRUE)))
  
  msoa_eval_data_type6 <- merge(msoa_eval_data_type5, resto_types)
  
  
  msoa_eval_data_type_final <- rbind(msoa_eval_data_type_final, msoa_eval_data_type6)
  
}

msoa_eval_data_type_final <- unique(msoa_eval_data_type_final)
#rm(msoa_eval_data_type_final)
#msoa_eval_data_type_final <- msoa_eval_data_type6

###Resto by price level ####

berlin_restos1_overview_price <- berlin_restos1 %>%group_by(price) %>%  
  summarize(restos = sum(dum, na.rm = TRUE))

berlin_restos1_overview_price1 <- subset(berlin_restos1_overview_price, price != "NA")

for(i in 1:nrow(berlin_restos1_overview_price1))
{  
  berlin_restos1_type <- subset(berlin_restos1,  (price == berlin_restos1_overview_price1$price[i]))
  
  resto_types <- subset(berlin_restos1_type, select = c(price))
  resto_types <- resto_types[!duplicated(resto_types$price), ]
  
  # berlin_restos1_type <- cbind(berlin_restos1_type, mile_1_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 1.6)) # number of points within distance 10000 km
  #berlin_restos1_type <- cbind(berlin_restos1_type, mile_05_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.8)) # number of points within distance 10000 km
  #berlin_restos1_type <- cbind(berlin_restos1_type, mile_025_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.4)) # number of points within distance 10000 km
  #berlin_restos1_type <- cbind(berlin_restos1_type, mile_0125_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.2)) # number of points within distance 10000 km
  
  #  berlin_restos1_type <- within(berlin_restos1_type, mile_1_all_type <- mile_1_all_type-1)
  # berlin_restos1_type <- within(berlin_restos1_type, mile_05_all_type <- mile_05_all_type-1)
  #  berlin_restos1_type <- within(berlin_restos1_type, mile_025_all_type <- mile_025_all_type-1)
  # berlin_restos1_type <- within(berlin_restos1_type, mile_0125_all_type <- mile_0125_all_type-1)
  
  #berlin_restos1_type1 <- subset(berlin_restos1_type, select = c(id, mile_1_all_type, mile_05_all_type, mile_025_all_type, mile_0125_all_type))
  
  #  berlin_restos2 <- merge(berlin_restos1, berlin_restos1_type1, by.x = "id", by.y = "id")
  #  berlin_retstos2 <- subset(berlin_restos2, is.na(id)==FALSE)
  
  #write.csv(berlin_restos1_type, "berlin restos1 type")
  
  #  avg1mile = median(mile_1_all), na.rm = TRUE,
  #  avg05mile = median(mile_05_all), na.rm = TRUE,
  #  avg025mile = median(mile_025_all), na.rm = TRUE,
  #  avg0125mile = median(mile_0125_all), na.rm = TRUE,
  #  avg1mile_type = median(mile_1_all_type), na.rm = TRUE,
  #  avg05mile_type = median(mile_05_all_type), na.rm = TRUE,
  #  avg025mile_type = median(mile_025_all_type), na.rm = TRUE,
  #  avg0125mile_type = median(mile_0125_all_type), na.rm = TRUE,  
  
  
  berlin_restos1_overview_zipaa_type <- berlin_restos1_type %>% group_by(`Greater London`, lsoa11cd, clusterNum) %>%  
    summarize(restos = sum(dum, na.rm = TRUE),
              avgpop = median(Pop, na.rm = TRUE),
              avgdensit = median(`Pop Density`), na.rm = TRUE,
              avginc = median(Income_Rank), na.rm = TRUE,
              avgMed_Age = median(Med_Age), na.rm = TRUE,
              
              avgpct_AGE_T0004 = median( pct_AGE_T0004), na.rm = TRUE,
              avgpct_AGE_T0509 = median( pct_AGE_T0509), na.rm = TRUE,
              avgpct_AGE_T1014 = median( pct_AGE_T1014), na.rm = TRUE,
              avgpct_AGE_T1519 = median( pct_AGE_T1519), na.rm = TRUE,
              avgpct_AGE_T2024 = median( pct_AGE_T2024), na.rm = TRUE,
              avgpct_AGE_T2529 = median( pct_AGE_T2529), na.rm = TRUE,
              avgpct_AGE_T3034 = median( pct_AGE_T3034), na.rm = TRUE,
              avgpct_AGE_T3539 = median( pct_AGE_T3539), na.rm = TRUE,
              avgpct_AGE_T4044 = median( pct_AGE_T4044), na.rm = TRUE,
              avgpct_AGE_T4549 = median( pct_AGE_T4549), na.rm = TRUE,
              avgpct_AGE_T5054 = median( pct_AGE_T5054), na.rm = TRUE,
              avgpct_AGE_T5559 = median( pct_AGE_T5559), na.rm = TRUE,
              avgpct_AGE_T6064 = median( pct_AGE_T6064), na.rm = TRUE,
              avgpct_AGE_T6569 = median( pct_AGE_T6569), na.rm = TRUE,
              avgpct_AGE_T7074 = median( pct_AGE_T7074), na.rm = TRUE,
              avgpct_AGE_T75PL = median( pct_AGE_T75PL), na.rm = TRUE,
              avgWhite = median( White), na.rm = TRUE,
              avgMixed = median( Mixed), na.rm = TRUE,
              avgAsian = median( Asian), na.rm = TRUE,
              avgAsian_Indian = median( Asian_Indian), na.rm = TRUE,
              avgAsian_Pakistani = median( Asian_Pakistani), na.rm = TRUE,
              avgAsian_Bangladeshi = median( Asian_Bangladeshi), na.rm = TRUE,
              avgAsian_Chinese = median( Asian_Chinese), na.rm = TRUE,
              avgOther_Asian = median( Other_Asian), na.rm = TRUE,
              avgBlack = median( Black), na.rm = TRUE,
              avgBlack_African = median( Black_African), na.rm = TRUE,
              avgBlack_Caribbean = median( Black_Caribbean), na.rm = TRUE,
              avgBlack_Other = median( Black_Other), na.rm = TRUE,
              avgOther = median( Other), na.rm = TRUE,
              avgOther_Arab = median( Other_Arab), na.rm = TRUE,
              avgOther_Other = median( Other_Other), na.rm = TRUE,
              avgIMD_Index = median( IMD_Index), na.rm = TRUE,
              avgIMD_Decile  = median( IMD_Decile ), na.rm = TRUE,
              avgIncome_Rank = median( Income_Rank), na.rm = TRUE,
              avgIncome_Decile = median( Income_Decile), na.rm = TRUE,
              avgForestry = median( `Forestry and logging`), na.rm = TRUE,
              avgFishing = median( `Fishing and aquaculture`), na.rm = TRUE,
              avgCoal = median( `Mining of coal and lignite`), na.rm = TRUE,
              avgOil = median( `Extraction of crude petroleum and natural gas`), na.rm = TRUE,
              avgOre = median( `Mining of metal ores`), na.rm = TRUE,
              avgmining = median( `Other mining and quarrying`), na.rm = TRUE,
              avgMiningSupport = median( `Mining support service activities`), na.rm = TRUE,
              avgFoodMan = median( `Manufacture of food products`), na.rm = TRUE,
              avgBevMan = median( `Manufacture of beverages`), na.rm = TRUE,
              avgTobMan = median( `Manufacture of tobacco products`), na.rm = TRUE,
              avgManTextile = median( `Manufacture of textiles`), na.rm = TRUE,
              avgManApparel = median( `Manufacture of wearing apparel`), na.rm = TRUE,
              avgManLeather = median( `Manufacture of leather and related products`), na.rm = TRUE,
              avgManWood = median( `Manufacture of wood and of products of wood and cork, except furniture;manufacture of articles of straw and plaiting materials`), na.rm = TRUE,
              avgManPaper = median( `Manufacture of paper and paper products`), na.rm = TRUE,
              avgPrinting = median( `Printing and reproduction of recorded media`), na.rm = TRUE,
              avgPetrolMan = median( `Manufacture of coke and refined petroleum products`), na.rm = TRUE,
              avgChemMan = median( `Manufacture of chemicals and chemical products`), na.rm = TRUE,
              avgPharmaMan = median( `Manufacture of basic pharmaceutical products and pharmaceutical preparations`), na.rm = TRUE,
              avgRubberMan = median( `Manufacture of rubber and plastic products`), na.rm = TRUE,
              avgMineralMan = median( `Manufacture of other non-metallic mineral products`), na.rm = TRUE,
              avgManBasicMetal = median( `Manufacture of basic metals`), na.rm = TRUE,
              avgFabMetal = median( `Manufacture of fabricated metal products, except machinery and equipment`), na.rm = TRUE,
              avgManComputers = median( `Manufacture of computer, electronic and optical products`), na.rm = TRUE,
              avgElectricalEquip = median( `Manufacture of electrical equipment`), na.rm = TRUE,
              avgManEquip = median( `Manufacture of machinery and equipment n.e.c.`), na.rm = TRUE,
              avgManCars = median( `Manufacture of motor vehicles, trailers and semi-trailers`), na.rm = TRUE,
              avgManOtherTrans = median( `Manufacture of other transport equipment`), na.rm = TRUE,
              avgFurnMan = median( `Manufacture of furniture`), na.rm = TRUE,
              avgOtherMan= median( `Other manufacturing`), na.rm = TRUE,
              avgRepairMach = median( `Repair and installation of machinery and equipment`), na.rm = TRUE,
              avgElectricity = median( `Electricity, gas, steam and air conditioning supply`), na.rm = TRUE,
              avgWaterTreat = median( `Water collection, treatment and supply`), na.rm = TRUE,
              avgSewer = median( `Sewerage`), na.rm = TRUE,
              avgWasteMgmt = median( `Waste collection, treatment and disposal activities; materials recovery`), na.rm = TRUE,
              avgRemedy = median( `Remediation activities and other waste management services. This division includes the provision of remediation services, i.e. the cleanup of contaminated buildings and sites, soil, surface or ground water.`), na.rm = TRUE,
              avgConstruction = median( `Construction of buildings`), na.rm = TRUE,
              avgCivilEng = median( `Civil engineering`), na.rm = TRUE,
              avgSpecialConst = median( `Specialised construction activities`), na.rm = TRUE,
              avgWholesaleRetail = median( `Wholesale and retail trade and repair of motor vehicles and motorcycles`), na.rm = TRUE,
              avgWholesale = median( `Wholesale trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
              avgRetail = median( `Retail trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
              avgPipeline = median( `Land transport and transport via pipelines`), na.rm = TRUE,
              avgWaterTxp = median( `Water transport`), na.rm = TRUE,
              avgAirTxp = median( `Air transport`), na.rm = TRUE,
              avgWarehouse = median( `Warehousing and support activities for transportation`), na.rm = TRUE,
              avgPost = median( `Postal and courier activities`), na.rm = TRUE,
              avgAccomodation = median( `Accommodation`), na.rm = TRUE,
              avgResto = median( `Food and beverage service activities`), na.rm = TRUE,
              avgPublishing = median( `Publishing activities`), na.rm = TRUE,
              avgMovieProd = median( `Motion picture, video and television programme production, sound recording and music publishing activities`), na.rm = TRUE,
              avgTV = median( `Programming and broadcasting activities`), na.rm = TRUE,
              avgTelecom = median( `Telecommunications`), na.rm = TRUE,
              avgConsult = median( `Computer programming, consultancy and related activities`), na.rm = TRUE,
              avgIT = median( `Information service activities`), na.rm = TRUE,
              avgFinAct = median( `Financial service activities, except insurance and pension funding`), na.rm = TRUE,
              avgInsAct = median( `Insurance, reinsurance and pension funding, except compulsory social security`), na.rm = TRUE,
              avgFinAuxAct = median( `Activities auxiliary to financial services and insurance activities`), na.rm = TRUE,
              avgRealtor = median( `Real estate activities`), na.rm = TRUE,
              avgLegal = median( `Legal and accounting activities`), na.rm = TRUE,
              avgHQ = median( `Activities of head offices; management consultancy activities`), na.rm = TRUE,
              avgArchitect = median( `Architectural and engineering activities; technical testing and analysis`), na.rm = TRUE,
              avgRD = median( `Scientific research and development`), na.rm = TRUE,
              avgMktg = median( `Advertising and market research`), na.rm = TRUE,
              avgProfAct = median( `Other professional, scientific and technical activities`), na.rm = TRUE,
              avgVet = median( `Veterinary activities`), na.rm = TRUE,
              avgRentLease = median( `Rental and leasing activities`), na.rm = TRUE,
              avgEmployAct = median( `Employment activities`), na.rm = TRUE,
              avgTravelTour = median( `Travel agency, tour operator and other reservation service and related activities`), na.rm = TRUE,
              avgSecurity = median( `Security and investigation activities`), na.rm = TRUE,
              avgLandscape = median( `Services to buildings and landscape activities`), na.rm = TRUE,
              avgOffice = median( `Office administrative, office support and other business support activities`), na.rm = TRUE,
              avgPublicAdmin = median( `Public administration and defence; compulsory social security`), na.rm = TRUE,
              avgEducation = median( `Education`), na.rm = TRUE,
              avgHHS = median( `Human health activities`), na.rm = TRUE,
              avgResCare = median( `Residential care activities`), na.rm = TRUE,
              avgSocWork = median( `Social work activities without accommodation`), na.rm = TRUE,
              avgArts = median( `Creative, arts and entertainment activities`), na.rm = TRUE,
              avgLibraries = median( `Libraries, archives, museums and other cultural activities`), na.rm = TRUE,
              avgCasino = median( `Gambling and betting activities`), na.rm = TRUE,
              avgSportsAct= median( `Sports activities and amusement and recreation activities`), na.rm = TRUE,
              avgClubs = median( `Activities of membership organisations`), na.rm = TRUE,
              avgRepairHH = median( `Repair of computers and personal and household goods`), na.rm = TRUE,
              avgOther = median( `Other personal service activities`), na.rm = TRUE,
              avgDomesticHelp = median( `Activities of households as employers of domestic personnel`), na.rm = TRUE,
              avgUndifHH = median( `Undifferentiated goods- and services-producing activities of private households for own use`), na.rm = TRUE,
              avgETs = median( `Activities of extraterritorial organisations and bodies`), na.rm = TRUE)
  
  
  cluster_type_data_melted <- melt(berlin_restos1_overview_zipaa_type, id=1:3)
  
  
  #write.csv(berlin_restos1_overview_zipaa_type, "berlin restos1 type overview")
  
  #  coravg1mile=cor(restos,avg1mile), 
  #  coravg05mile=cor(restos,avg05mile), 
  #  coravg025mile=cor(restos,avg025mile), 
  #  coravg0125mile=cor(restos,avg0125mile), 
  #  coravg1mile_type=cor(restos,avg1mile_type), 
  #  coravg05mile_type=cor(restos,avg05mile_type), 
  #  coravg025mile_type=cor(restos,avg025mile_type), 
  #  coravg0125mile_type=cor(restos,avg0125mile_type), 
  
  corr_by_cluster_type <- berlin_restos1_overview_zipaa_type %>% group_by(clusterNum) %>%
    summarize(coravgpop=cor(restos,avgpop), 
              coravgdensit=cor(restos,avgdensit), 
              coravginc=cor(restos,avginc), 
              coravgMed_Age=cor(restos,avgMed_Age), 
              
              coravgpct_AGE_T0004=cor(restos,avgpct_AGE_T0004), 
              coravgpct_AGE_T0509=cor(restos,avgpct_AGE_T0509), 
              coravgpct_AGE_T1014=cor(restos,avgpct_AGE_T1014), 
              coravgpct_AGE_T1519=cor(restos,avgpct_AGE_T1519), 
              coravgpct_AGE_T2024=cor(restos,avgpct_AGE_T2024), 
              coravgpct_AGE_T2529=cor(restos,avgpct_AGE_T2529), 
              coravgpct_AGE_T3034=cor(restos,avgpct_AGE_T3034), 
              coravgpct_AGE_T3539=cor(restos,avgpct_AGE_T3539), 
              coravgpct_AGE_T4044=cor(restos,avgpct_AGE_T4044), 
              coravgpct_AGE_T4549=cor(restos,avgpct_AGE_T4549), 
              coravgpct_AGE_T5054=cor(restos,avgpct_AGE_T5054), 
              coravgpct_AGE_T5559=cor(restos,avgpct_AGE_T5559), 
              coravgpct_AGE_T6064=cor(restos,avgpct_AGE_T6064), 
              coravgpct_AGE_T6569=cor(restos,avgpct_AGE_T6569), 
              coravgpct_AGE_T7074=cor(restos,avgpct_AGE_T7074), 
              coravgpct_AGE_T75PL=cor(restos,avgpct_AGE_T75PL), 
              coravgWhite=cor(restos,avgWhite), 
              coravgMixed=cor(restos,avgMixed), 
              coravgAsian=cor(restos,avgAsian), 
              coravgAsian_Indian=cor(restos,avgAsian_Indian), 
              coravgAsian_Pakistani=cor(restos,avgAsian_Pakistani), 
              coravgAsian_Bangladeshi=cor(restos,avgAsian_Bangladeshi), 
              coravgAsian_Chinese=cor(restos,avgAsian_Chinese), 
              coravgOther_Asian=cor(restos,avgOther_Asian), 
              coravgBlack=cor(restos,avgBlack), 
              coravgBlack_African=cor(restos,avgBlack_African), 
              coravgBlack_Caribbean=cor(restos,avgBlack_Caribbean), 
              coravgBlack_Other=cor(restos,avgBlack_Other), 
              coravgOther=cor(restos,avgOther), 
              coravgOther_Arab=cor(restos,avgOther_Arab), 
              coravgOther_Other=cor(restos,avgOther_Other), 
              coravgIMD_Index=cor(restos,avgIMD_Index), 
              coravgIMD_Decile=cor(restos,avgIMD_Decile), 
              coravgIncome_Rank=cor(restos,avgIncome_Rank), 
              coravgIncome_Decile=cor(restos,avgIncome_Decile), 
              coravgForestry=cor(restos,avgForestry), 
              coravgFishing=cor(restos,avgFishing), 
              coravgCoal=cor(restos,avgCoal), 
              coravgOil=cor(restos,avgOil), 
              coravgOre=cor(restos,avgOre), 
              coravgmining=cor(restos,avgmining), 
              coravgMiningSupport=cor(restos,avgMiningSupport), 
              coravgFoodMan=cor(restos,avgFoodMan), 
              coravgBevMan=cor(restos,avgBevMan), 
              coravgTobMan=cor(restos,avgTobMan), 
              coravgManTextile=cor(restos,avgManTextile), 
              coravgManApparel=cor(restos,avgManApparel), 
              coravgManLeather=cor(restos,avgManLeather), 
              coravgManWood=cor(restos,avgManWood), 
              coravgManPaper=cor(restos,avgManPaper), 
              coravgPrinting=cor(restos,avgPrinting), 
              coravgPetrolMan=cor(restos,avgPetrolMan), 
              coravgChemMan=cor(restos,avgChemMan), 
              coravgPharmaMan=cor(restos,avgPharmaMan), 
              coravgRubberMan=cor(restos,avgRubberMan), 
              coravgMineralMan=cor(restos,avgMineralMan), 
              coravgManBasicMetal=cor(restos,avgManBasicMetal), 
              coravgFabMetal=cor(restos,avgFabMetal), 
              coravgManComputers=cor(restos,avgManComputers), 
              coravgElectricalEquip=cor(restos,avgElectricalEquip), 
              coravgManEquip=cor(restos,avgManEquip), 
              coravgManCars=cor(restos,avgManCars), 
              coravgManOtherTrans=cor(restos,avgManOtherTrans), 
              coravgFurnMan=cor(restos,avgFurnMan), 
              coravgOtherMan=cor(restos,avgOtherMan), 
              coravgRepairMach=cor(restos,avgRepairMach), 
              coravgElectricity=cor(restos,avgElectricity), 
              coravgWaterTreat=cor(restos,avgWaterTreat), 
              coravgSewer=cor(restos,avgSewer), 
              coravgWasteMgmt=cor(restos,avgWasteMgmt), 
              coravgRemedy=cor(restos,avgRemedy), 
              coravgConstruction=cor(restos,avgConstruction), 
              coravgCivilEng=cor(restos,avgCivilEng), 
              coravgSpecialConst=cor(restos,avgSpecialConst), 
              coravgWholesaleRetail=cor(restos,avgWholesaleRetail), 
              coravgWholesale=cor(restos,avgWholesale), 
              coravgRetail=cor(restos,avgRetail), 
              coravgPipeline=cor(restos,avgPipeline), 
              coravgWaterTxp=cor(restos,avgWaterTxp), 
              coravgAirTxp=cor(restos,avgAirTxp), 
              coravgWarehouse=cor(restos,avgWarehouse), 
              coravgPost=cor(restos,avgPost), 
              coravgAccomodation=cor(restos,avgAccomodation), 
              coravgResto=cor(restos,avgResto), 
              coravgPublishing=cor(restos,avgPublishing), 
              coravgMovieProd=cor(restos,avgMovieProd), 
              coravgTV=cor(restos,avgTV), 
              coravgTelecom=cor(restos,avgTelecom), 
              coravgConsult=cor(restos,avgConsult), 
              coravgIT=cor(restos,avgIT), 
              coravgFinAct=cor(restos,avgFinAct), 
              coravgInsAct=cor(restos,avgInsAct), 
              coravgFinAuxAct=cor(restos,avgFinAuxAct), 
              coravgRealtor=cor(restos,avgRealtor), 
              coravgLegal=cor(restos,avgLegal), 
              coravgHQ=cor(restos,avgHQ), 
              coravgArchitect=cor(restos,avgArchitect), 
              coravgRD=cor(restos,avgRD), 
              coravgMktg=cor(restos,avgMktg), 
              coravgProfAct=cor(restos,avgProfAct), 
              coravgVet=cor(restos,avgVet), 
              coravgRentLease=cor(restos,avgRentLease), 
              coravgEmployAct=cor(restos,avgEmployAct), 
              coravgTravelTour=cor(restos,avgTravelTour), 
              coravgSecurity=cor(restos,avgSecurity), 
              coravgLandscape=cor(restos,avgLandscape), 
              coravgOffice=cor(restos,avgOffice), 
              coravgPublicAdmin=cor(restos,avgPublicAdmin), 
              coravgEducation=cor(restos,avgEducation), 
              coravgHHS=cor(restos,avgHHS), 
              coravgResCare=cor(restos,avgResCare), 
              coravgSocWork=cor(restos,avgSocWork), 
              coravgArts=cor(restos,avgArts), 
              coravgLibraries=cor(restos,avgLibraries), 
              coravgCasino=cor(restos,avgCasino), 
              coravgSportsAct=cor(restos,avgSportsAct), 
              coravgClubs=cor(restos,avgClubs), 
              coravgRepairHH=cor(restos,avgRepairHH), 
              coravgOther=cor(restos,avgOther), 
              coravgDomesticHelp=cor(restos,avgDomesticHelp), 
              coravgUndifHH=cor(restos,avgUndifHH), 
              coravgETs=cor(restos,avgETs))
  
  
  corr_by_cluster_type_melted <- melt(corr_by_cluster_type, id=1)
  corr_by_cluster_type_melted <- rename(corr_by_cluster_type_melted, correlation = value)
  corr_by_cluster_type_melted <- within(corr_by_cluster_type_melted, variable <- substr(variable, 4,30))
  
  rankings_type<- corr_by_cluster_type_melted %>%
    group_by(clusterNum) %>%
    mutate(good_ranks = order(order(abs(correlation), decreasing=TRUE)))
  
  
  msoa_data_eval_type_1 <- merge(cluster_data_melted, rankings_type, by = c("clusterNum", "variable"))
  
  
  msoa_data_eval_type <- merge(msoa_data_eval_type_1, cluster_avg_data_melted, by = c("clusterNum", "variable"))
  
  msoa_data_eval_type <- subset(msoa_data_eval_type, is.na(correlation)==FALSE)
  
  msoa_data_eval_type <- subset(msoa_data_eval_type, is.na(correlation)==FALSE)
  msoa_data_eval_type <- msoa_data_eval_type %>% rename(value = value.x)
  msoa_data_eval_type <- msoa_data_eval_type %>% rename(avg = value.y)
  
  msoa_data_eval_type <- within(msoa_data_eval_type, factordif <- (value - avg)*correlation)
  #msoa_eval_data_type <- subset(msoa_eval_data_type, good_ranks < 20)
  
  
  msoa_eval_data_type1 <-   msoa_data_eval_type %>%group_by(clusterNum, LSOA_Code) %>%  
    summarize(score = sum(factordif, na.rm = TRUE))
  
  msoa_min_type <- min(msoa_eval_data_type1$score)
  
  msoa_eval_data_type2 <- merge(msoa_eval_data_type1, msoa_min_type)
  msoa_eval_data_type2 <- within(msoa_eval_data_type2, revised_score <- score-y)
  
  msoa_max_type <- max(msoa_eval_data_type2$revised_score)
  msoa_eval_data_type2 <- subset(msoa_eval_data_type2, select=-c(y))
  
  msoa_eval_data_type3 <- merge(msoa_eval_data_type2, msoa_max_type)
  msoa_eval_data_type3 <- within(msoa_eval_data_type3, normalized_score <- 100*(revised_score/y))
  
  msoa_data <- subset(UK_Demographic_Data_Master, select=c(LSOA_Code, LSOA_Name))
  msoa_data <- unique.data.frame(msoa_data)
  
  msoa_eval_data_type4 <- merge(msoa_eval_data_type3, msoa_data, by.x = ("LSOA_Code"), by.y = c("LSOA_Code"))
  
  msoa_eval_data_type5 <- msoa_eval_data_type4 %>%  mutate(good_ranks = order(order(abs(score), decreasing=TRUE)))
  
  msoa_eval_data_type6 <- merge(msoa_eval_data_type5, resto_types)
  
  
  msoa_eval_data_type_final_price <- rbind(msoa_eval_data_type_final_price, msoa_eval_data_type6)
  
}

msoa_eval_data_type_final_price <- unique(msoa_eval_data_type_final_price)
#msoa_eval_data_type_final_price <- msoa_eval_data_type6
#rm(msoa_eval_data_type_final_price)



### Resto by Price and Type ####
for(i in 12:nrow(berlin_restos1_overview_type_price1))
{  
  berlin_restos1_type <- subset(berlin_restos1,  (category_alias == berlin_restos1_overview_type_price1$category_alias[i] & price==berlin_restos1_overview_type_price1$price[i]))
  
  resto_types <- subset(berlin_restos1_type, select = c(category_alias, price))
  resto_types <- resto_types[!duplicated(resto_types$category_alias, resto_types$price), ]
  
  #berlin_restos1_type <- cbind(berlin_restos1_type, mile_1_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 1.6)) # number of points within distance 10000 km
  #berlin_restos1_type <- cbind(berlin_restos1_type, mile_05_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.8)) # number of points within distance 10000 km
  #berlin_restos1_type <- cbind(berlin_restos1_type, mile_025_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.4)) # number of points within distance 10000 km
  #berlin_restos1_type <- cbind(berlin_restos1_type, mile_0125_all_type=rowSums(distm (berlin_restos1_type[,161:162], fun = distHaversine) / 1000 <= 0.2)) # number of points within distance 10000 km
  
  #berlin_restos1_type <- within(berlin_restos1_type, mile_1_all_type <- mile_1_all_type-1)
  #berlin_restos1_type <- within(berlin_restos1_type, mile_05_all_type <- mile_05_all_type-1)
  #berlin_restos1_type <- within(berlin_restos1_type, mile_025_all_type <- mile_025_all_type-1)
  #berlin_restos1_type <- within(berlin_restos1_type, mile_0125_all_type <- mile_0125_all_type-1)
  
  #berlin_restos1_type1 <- subset(berlin_restos1_type, select = c(id, mile_1_all_type, mile_05_all_type, mile_025_all_type, mile_0125_all_type))
  
  #berlin_restos2 <- merge(berlin_restos1, berlin_restos1_type1, by.x = "id", by.y = "id", all.x = TRUE)
  #berlin_retstos2 <- subset(berlin_restos2, is.na(id)==FALSE)
  #write.csv(berlin_restos1_type, "berlin restos1 type")
  
  #avg1mile = median(mile_1_all), na.rm = TRUE,
  #avg05mile = median(mile_05_all), na.rm = TRUE,
  #avg025mile = median(mile_025_all), na.rm = TRUE,
  #avg0125mile = median(mile_0125_all), na.rm = TRUE,
  #avg1mile_type = median(mile_1_all_type), na.rm = TRUE,
  #avg05mile_type = median(mile_05_all_type), na.rm = TRUE,
  #avg025mile_type = median(mile_025_all_type), na.rm = TRUE,
  #avg0125mile_type = median(mile_0125_all_type), na.rm = TRUE,
  
  berlin_restos1_overview_zipaa_type <- berlin_restos1_type %>% group_by(`Greater London`, lsoa11cd, clusterNum) %>%  
    summarize(restos = sum(dum, na.rm = TRUE),
              avgpop = median(Pop, na.rm = TRUE),
              avgdensit = median(`Pop Density`), na.rm = TRUE,
              avginc = median(Income_Rank), na.rm = TRUE,
              avgMed_Age = median(Med_Age), na.rm = TRUE,
              avgpct_AGE_T0004 = median( pct_AGE_T0004), na.rm = TRUE,
              avgpct_AGE_T0509 = median( pct_AGE_T0509), na.rm = TRUE,
              avgpct_AGE_T1014 = median( pct_AGE_T1014), na.rm = TRUE,
              avgpct_AGE_T1519 = median( pct_AGE_T1519), na.rm = TRUE,
              avgpct_AGE_T2024 = median( pct_AGE_T2024), na.rm = TRUE,
              avgpct_AGE_T2529 = median( pct_AGE_T2529), na.rm = TRUE,
              avgpct_AGE_T3034 = median( pct_AGE_T3034), na.rm = TRUE,
              avgpct_AGE_T3539 = median( pct_AGE_T3539), na.rm = TRUE,
              avgpct_AGE_T4044 = median( pct_AGE_T4044), na.rm = TRUE,
              avgpct_AGE_T4549 = median( pct_AGE_T4549), na.rm = TRUE,
              avgpct_AGE_T5054 = median( pct_AGE_T5054), na.rm = TRUE,
              avgpct_AGE_T5559 = median( pct_AGE_T5559), na.rm = TRUE,
              avgpct_AGE_T6064 = median( pct_AGE_T6064), na.rm = TRUE,
              avgpct_AGE_T6569 = median( pct_AGE_T6569), na.rm = TRUE,
              avgpct_AGE_T7074 = median( pct_AGE_T7074), na.rm = TRUE,
              avgpct_AGE_T75PL = median( pct_AGE_T75PL), na.rm = TRUE,
              avgWhite = median( White), na.rm = TRUE,
              avgMixed = median( Mixed), na.rm = TRUE,
              avgAsian = median( Asian), na.rm = TRUE,
              avgAsian_Indian = median( Asian_Indian), na.rm = TRUE,
              avgAsian_Pakistani = median( Asian_Pakistani), na.rm = TRUE,
              avgAsian_Bangladeshi = median( Asian_Bangladeshi), na.rm = TRUE,
              avgAsian_Chinese = median( Asian_Chinese), na.rm = TRUE,
              avgOther_Asian = median( Other_Asian), na.rm = TRUE,
              avgBlack = median( Black), na.rm = TRUE,
              avgBlack_African = median( Black_African), na.rm = TRUE,
              avgBlack_Caribbean = median( Black_Caribbean), na.rm = TRUE,
              avgBlack_Other = median( Black_Other), na.rm = TRUE,
              avgOther = median( Other), na.rm = TRUE,
              avgOther_Arab = median( Other_Arab), na.rm = TRUE,
              avgOther_Other = median( Other_Other), na.rm = TRUE,
              avgIMD_Index = median( IMD_Index), na.rm = TRUE,
              avgIMD_Decile  = median( IMD_Decile ), na.rm = TRUE,
              avgIncome_Rank = median( Income_Rank), na.rm = TRUE,
              avgIncome_Decile = median( Income_Decile), na.rm = TRUE,
              avgForestry = median( `Forestry and logging`), na.rm = TRUE,
              avgFishing = median( `Fishing and aquaculture`), na.rm = TRUE,
              avgCoal = median( `Mining of coal and lignite`), na.rm = TRUE,
              avgOil = median( `Extraction of crude petroleum and natural gas`), na.rm = TRUE,
              avgOre = median( `Mining of metal ores`), na.rm = TRUE,
              avgmining = median( `Other mining and quarrying`), na.rm = TRUE,
              avgMiningSupport = median( `Mining support service activities`), na.rm = TRUE,
              avgFoodMan = median( `Manufacture of food products`), na.rm = TRUE,
              avgBevMan = median( `Manufacture of beverages`), na.rm = TRUE,
              avgTobMan = median( `Manufacture of tobacco products`), na.rm = TRUE,
              avgManTextile = median( `Manufacture of textiles`), na.rm = TRUE,
              avgManApparel = median( `Manufacture of wearing apparel`), na.rm = TRUE,
              avgManLeather = median( `Manufacture of leather and related products`), na.rm = TRUE,
              avgManWood = median( `Manufacture of wood and of products of wood and cork, except furniture;manufacture of articles of straw and plaiting materials`), na.rm = TRUE,
              avgManPaper = median( `Manufacture of paper and paper products`), na.rm = TRUE,
              avgPrinting = median( `Printing and reproduction of recorded media`), na.rm = TRUE,
              avgPetrolMan = median( `Manufacture of coke and refined petroleum products`), na.rm = TRUE,
              avgChemMan = median( `Manufacture of chemicals and chemical products`), na.rm = TRUE,
              avgPharmaMan = median( `Manufacture of basic pharmaceutical products and pharmaceutical preparations`), na.rm = TRUE,
              avgRubberMan = median( `Manufacture of rubber and plastic products`), na.rm = TRUE,
              avgMineralMan = median( `Manufacture of other non-metallic mineral products`), na.rm = TRUE,
              avgManBasicMetal = median( `Manufacture of basic metals`), na.rm = TRUE,
              avgFabMetal = median( `Manufacture of fabricated metal products, except machinery and equipment`), na.rm = TRUE,
              avgManComputers = median( `Manufacture of computer, electronic and optical products`), na.rm = TRUE,
              avgElectricalEquip = median( `Manufacture of electrical equipment`), na.rm = TRUE,
              avgManEquip = median( `Manufacture of machinery and equipment n.e.c.`), na.rm = TRUE,
              avgManCars = median( `Manufacture of motor vehicles, trailers and semi-trailers`), na.rm = TRUE,
              avgManOtherTrans = median( `Manufacture of other transport equipment`), na.rm = TRUE,
              avgFurnMan = median( `Manufacture of furniture`), na.rm = TRUE,
              avgOtherMan= median( `Other manufacturing`), na.rm = TRUE,
              avgRepairMach = median( `Repair and installation of machinery and equipment`), na.rm = TRUE,
              avgElectricity = median( `Electricity, gas, steam and air conditioning supply`), na.rm = TRUE,
              avgWaterTreat = median( `Water collection, treatment and supply`), na.rm = TRUE,
              avgSewer = median( `Sewerage`), na.rm = TRUE,
              avgWasteMgmt = median( `Waste collection, treatment and disposal activities; materials recovery`), na.rm = TRUE,
              avgRemedy = median( `Remediation activities and other waste management services. This division includes the provision of remediation services, i.e. the cleanup of contaminated buildings and sites, soil, surface or ground water.`), na.rm = TRUE,
              avgConstruction = median( `Construction of buildings`), na.rm = TRUE,
              avgCivilEng = median( `Civil engineering`), na.rm = TRUE,
              avgSpecialConst = median( `Specialised construction activities`), na.rm = TRUE,
              avgWholesaleRetail = median( `Wholesale and retail trade and repair of motor vehicles and motorcycles`), na.rm = TRUE,
              avgWholesale = median( `Wholesale trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
              avgRetail = median( `Retail trade, except of motor vehicles and motorcycles`), na.rm = TRUE,
              avgPipeline = median( `Land transport and transport via pipelines`), na.rm = TRUE,
              avgWaterTxp = median( `Water transport`), na.rm = TRUE,
              avgAirTxp = median( `Air transport`), na.rm = TRUE,
              avgWarehouse = median( `Warehousing and support activities for transportation`), na.rm = TRUE,
              avgPost = median( `Postal and courier activities`), na.rm = TRUE,
              avgAccomodation = median( `Accommodation`), na.rm = TRUE,
              avgResto = median( `Food and beverage service activities`), na.rm = TRUE,
              avgPublishing = median( `Publishing activities`), na.rm = TRUE,
              avgMovieProd = median( `Motion picture, video and television programme production, sound recording and music publishing activities`), na.rm = TRUE,
              avgTV = median( `Programming and broadcasting activities`), na.rm = TRUE,
              avgTelecom = median( `Telecommunications`), na.rm = TRUE,
              avgConsult = median( `Computer programming, consultancy and related activities`), na.rm = TRUE,
              avgIT = median( `Information service activities`), na.rm = TRUE,
              avgFinAct = median( `Financial service activities, except insurance and pension funding`), na.rm = TRUE,
              avgInsAct = median( `Insurance, reinsurance and pension funding, except compulsory social security`), na.rm = TRUE,
              avgFinAuxAct = median( `Activities auxiliary to financial services and insurance activities`), na.rm = TRUE,
              avgRealtor = median( `Real estate activities`), na.rm = TRUE,
              avgLegal = median( `Legal and accounting activities`), na.rm = TRUE,
              avgHQ = median( `Activities of head offices; management consultancy activities`), na.rm = TRUE,
              avgArchitect = median( `Architectural and engineering activities; technical testing and analysis`), na.rm = TRUE,
              avgRD = median( `Scientific research and development`), na.rm = TRUE,
              avgMktg = median( `Advertising and market research`), na.rm = TRUE,
              avgProfAct = median( `Other professional, scientific and technical activities`), na.rm = TRUE,
              avgVet = median( `Veterinary activities`), na.rm = TRUE,
              avgRentLease = median( `Rental and leasing activities`), na.rm = TRUE,
              avgEmployAct = median( `Employment activities`), na.rm = TRUE,
              avgTravelTour = median( `Travel agency, tour operator and other reservation service and related activities`), na.rm = TRUE,
              avgSecurity = median( `Security and investigation activities`), na.rm = TRUE,
              avgLandscape = median( `Services to buildings and landscape activities`), na.rm = TRUE,
              avgOffice = median( `Office administrative, office support and other business support activities`), na.rm = TRUE,
              avgPublicAdmin = median( `Public administration and defence; compulsory social security`), na.rm = TRUE,
              avgEducation = median( `Education`), na.rm = TRUE,
              avgHHS = median( `Human health activities`), na.rm = TRUE,
              avgResCare = median( `Residential care activities`), na.rm = TRUE,
              avgSocWork = median( `Social work activities without accommodation`), na.rm = TRUE,
              avgArts = median( `Creative, arts and entertainment activities`), na.rm = TRUE,
              avgLibraries = median( `Libraries, archives, museums and other cultural activities`), na.rm = TRUE,
              avgCasino = median( `Gambling and betting activities`), na.rm = TRUE,
              avgSportsAct= median( `Sports activities and amusement and recreation activities`), na.rm = TRUE,
              avgClubs = median( `Activities of membership organisations`), na.rm = TRUE,
              avgRepairHH = median( `Repair of computers and personal and household goods`), na.rm = TRUE,
              avgOther = median( `Other personal service activities`), na.rm = TRUE,
              avgDomesticHelp = median( `Activities of households as employers of domestic personnel`), na.rm = TRUE,
              avgUndifHH = median( `Undifferentiated goods- and services-producing activities of private households for own use`), na.rm = TRUE,
              avgETs = median( `Activities of extraterritorial organisations and bodies`), na.rm = TRUE)
  
  
  cluster_type_data_melted <- melt(berlin_restos1_overview_zipaa_type, id=1:3)
  
  
  #write.csv(berlin_restos1_overview_zipaa_type, "berlin restos1 type overview")
  #coravg1mile=cor(restos,avg1mile), 
  #coravg05mile=cor(restos,avg05mile), 
  #coravg025mile=cor(restos,avg025mile), 
  #coravg0125mile=cor(restos,avg0125mile), 
  #coravg1mile_type=cor(restos,avg1mile_type), 
  #coravg05mile_type=cor(restos,avg05mile_type), 
  #coravg025mile_type=cor(restos,avg025mile_type), 
  #coravg0125mile_type=cor(restos,avg0125mile_type), 
  
  corr_by_cluster_type <- berlin_restos1_overview_zipaa_type %>% group_by(clusterNum) %>%
    summarize(coravgpop=cor(restos,avgpop), 
              coravgdensit=cor(restos,avgdensit), 
              coravginc=cor(restos,avginc), 
              coravgMed_Age=cor(restos,avgMed_Age), 
              coravgpct_AGE_T0004=cor(restos,avgpct_AGE_T0004), 
              coravgpct_AGE_T0509=cor(restos,avgpct_AGE_T0509), 
              coravgpct_AGE_T1014=cor(restos,avgpct_AGE_T1014), 
              coravgpct_AGE_T1519=cor(restos,avgpct_AGE_T1519), 
              coravgpct_AGE_T2024=cor(restos,avgpct_AGE_T2024), 
              coravgpct_AGE_T2529=cor(restos,avgpct_AGE_T2529), 
              coravgpct_AGE_T3034=cor(restos,avgpct_AGE_T3034), 
              coravgpct_AGE_T3539=cor(restos,avgpct_AGE_T3539), 
              coravgpct_AGE_T4044=cor(restos,avgpct_AGE_T4044), 
              coravgpct_AGE_T4549=cor(restos,avgpct_AGE_T4549), 
              coravgpct_AGE_T5054=cor(restos,avgpct_AGE_T5054), 
              coravgpct_AGE_T5559=cor(restos,avgpct_AGE_T5559), 
              coravgpct_AGE_T6064=cor(restos,avgpct_AGE_T6064), 
              coravgpct_AGE_T6569=cor(restos,avgpct_AGE_T6569), 
              coravgpct_AGE_T7074=cor(restos,avgpct_AGE_T7074), 
              coravgpct_AGE_T75PL=cor(restos,avgpct_AGE_T75PL), 
              coravgWhite=cor(restos,avgWhite), 
              coravgMixed=cor(restos,avgMixed), 
              coravgAsian=cor(restos,avgAsian), 
              coravgAsian_Indian=cor(restos,avgAsian_Indian), 
              coravgAsian_Pakistani=cor(restos,avgAsian_Pakistani), 
              coravgAsian_Bangladeshi=cor(restos,avgAsian_Bangladeshi), 
              coravgAsian_Chinese=cor(restos,avgAsian_Chinese), 
              coravgOther_Asian=cor(restos,avgOther_Asian), 
              coravgBlack=cor(restos,avgBlack), 
              coravgBlack_African=cor(restos,avgBlack_African), 
              coravgBlack_Caribbean=cor(restos,avgBlack_Caribbean), 
              coravgBlack_Other=cor(restos,avgBlack_Other), 
              coravgOther=cor(restos,avgOther), 
              coravgOther_Arab=cor(restos,avgOther_Arab), 
              coravgOther_Other=cor(restos,avgOther_Other), 
              coravgIMD_Index=cor(restos,avgIMD_Index), 
              coravgIMD_Decile=cor(restos,avgIMD_Decile), 
              coravgIncome_Rank=cor(restos,avgIncome_Rank), 
              coravgIncome_Decile=cor(restos,avgIncome_Decile), 
              coravgForestry=cor(restos,avgForestry), 
              coravgFishing=cor(restos,avgFishing), 
              coravgCoal=cor(restos,avgCoal), 
              coravgOil=cor(restos,avgOil), 
              coravgOre=cor(restos,avgOre), 
              coravgmining=cor(restos,avgmining), 
              coravgMiningSupport=cor(restos,avgMiningSupport), 
              coravgFoodMan=cor(restos,avgFoodMan), 
              coravgBevMan=cor(restos,avgBevMan), 
              coravgTobMan=cor(restos,avgTobMan), 
              coravgManTextile=cor(restos,avgManTextile), 
              coravgManApparel=cor(restos,avgManApparel), 
              coravgManLeather=cor(restos,avgManLeather), 
              coravgManWood=cor(restos,avgManWood), 
              coravgManPaper=cor(restos,avgManPaper), 
              coravgPrinting=cor(restos,avgPrinting), 
              coravgPetrolMan=cor(restos,avgPetrolMan), 
              coravgChemMan=cor(restos,avgChemMan), 
              coravgPharmaMan=cor(restos,avgPharmaMan), 
              coravgRubberMan=cor(restos,avgRubberMan), 
              coravgMineralMan=cor(restos,avgMineralMan), 
              coravgManBasicMetal=cor(restos,avgManBasicMetal), 
              coravgFabMetal=cor(restos,avgFabMetal), 
              coravgManComputers=cor(restos,avgManComputers), 
              coravgElectricalEquip=cor(restos,avgElectricalEquip), 
              coravgManEquip=cor(restos,avgManEquip), 
              coravgManCars=cor(restos,avgManCars), 
              coravgManOtherTrans=cor(restos,avgManOtherTrans), 
              coravgFurnMan=cor(restos,avgFurnMan), 
              coravgOtherMan=cor(restos,avgOtherMan), 
              coravgRepairMach=cor(restos,avgRepairMach), 
              coravgElectricity=cor(restos,avgElectricity), 
              coravgWaterTreat=cor(restos,avgWaterTreat), 
              coravgSewer=cor(restos,avgSewer), 
              coravgWasteMgmt=cor(restos,avgWasteMgmt), 
              coravgRemedy=cor(restos,avgRemedy), 
              coravgConstruction=cor(restos,avgConstruction), 
              coravgCivilEng=cor(restos,avgCivilEng), 
              coravgSpecialConst=cor(restos,avgSpecialConst), 
              coravgWholesaleRetail=cor(restos,avgWholesaleRetail), 
              coravgWholesale=cor(restos,avgWholesale), 
              coravgRetail=cor(restos,avgRetail), 
              coravgPipeline=cor(restos,avgPipeline), 
              coravgWaterTxp=cor(restos,avgWaterTxp), 
              coravgAirTxp=cor(restos,avgAirTxp), 
              coravgWarehouse=cor(restos,avgWarehouse), 
              coravgPost=cor(restos,avgPost), 
              coravgAccomodation=cor(restos,avgAccomodation), 
              coravgResto=cor(restos,avgResto), 
              coravgPublishing=cor(restos,avgPublishing), 
              coravgMovieProd=cor(restos,avgMovieProd), 
              coravgTV=cor(restos,avgTV), 
              coravgTelecom=cor(restos,avgTelecom), 
              coravgConsult=cor(restos,avgConsult), 
              coravgIT=cor(restos,avgIT), 
              coravgFinAct=cor(restos,avgFinAct), 
              coravgInsAct=cor(restos,avgInsAct), 
              coravgFinAuxAct=cor(restos,avgFinAuxAct), 
              coravgRealtor=cor(restos,avgRealtor), 
              coravgLegal=cor(restos,avgLegal), 
              coravgHQ=cor(restos,avgHQ), 
              coravgArchitect=cor(restos,avgArchitect), 
              coravgRD=cor(restos,avgRD), 
              coravgMktg=cor(restos,avgMktg), 
              coravgProfAct=cor(restos,avgProfAct), 
              coravgVet=cor(restos,avgVet), 
              coravgRentLease=cor(restos,avgRentLease), 
              coravgEmployAct=cor(restos,avgEmployAct), 
              coravgTravelTour=cor(restos,avgTravelTour), 
              coravgSecurity=cor(restos,avgSecurity), 
              coravgLandscape=cor(restos,avgLandscape), 
              coravgOffice=cor(restos,avgOffice), 
              coravgPublicAdmin=cor(restos,avgPublicAdmin), 
              coravgEducation=cor(restos,avgEducation), 
              coravgHHS=cor(restos,avgHHS), 
              coravgResCare=cor(restos,avgResCare), 
              coravgSocWork=cor(restos,avgSocWork), 
              coravgArts=cor(restos,avgArts), 
              coravgLibraries=cor(restos,avgLibraries), 
              coravgCasino=cor(restos,avgCasino), 
              coravgSportsAct=cor(restos,avgSportsAct), 
              coravgClubs=cor(restos,avgClubs), 
              coravgRepairHH=cor(restos,avgRepairHH), 
              coravgOther=cor(restos,avgOther), 
              coravgDomesticHelp=cor(restos,avgDomesticHelp), 
              coravgUndifHH=cor(restos,avgUndifHH), 
              coravgETs=cor(restos,avgETs))
  
  
  corr_by_cluster_type_melted <- melt(corr_by_cluster_type, id=1)
  corr_by_cluster_type_melted <- rename(corr_by_cluster_type_melted, correlation = value)
  corr_by_cluster_type_melted <- within(corr_by_cluster_type_melted, variable <- substr(variable, 4,30))
  
  rankings_type<- corr_by_cluster_type_melted %>%
    group_by(clusterNum) %>%
    mutate(good_ranks = order(order(abs(correlation), decreasing=TRUE)))
  
  
  msoa_data_eval_type_1 <- merge(cluster_data_melted, rankings_type, by = c("clusterNum", "variable"))
  
  
  msoa_data_eval_type <- merge(msoa_data_eval_type_1, cluster_avg_data_melted, by = c("clusterNum", "variable"))
  
  msoa_data_eval_type <- subset(msoa_data_eval_type, is.na(correlation)==FALSE)
  
  msoa_data_eval_type <- subset(msoa_data_eval_type, is.na(correlation)==FALSE)
  msoa_data_eval_type <- msoa_data_eval_type %>% rename(value = value.x)
  msoa_data_eval_type <- msoa_data_eval_type %>% rename(avg = value.y)
  
  msoa_data_eval_type <- within(msoa_data_eval_type, factordif <- (value - avg)*correlation)
  #msoa_eval_data_type <- subset(msoa_eval_data_type, good_ranks < 20)
  
  
  msoa_eval_data_type1 <-   msoa_data_eval_type %>%group_by(clusterNum, LSOA_Code) %>%  
    summarize(score = sum(factordif, na.rm = TRUE))
  
  msoa_min_type <- min(msoa_eval_data_type1$score)
  
  msoa_eval_data_type2 <- merge(msoa_eval_data_type1, msoa_min_type)
  msoa_eval_data_type2 <- within(msoa_eval_data_type2, revised_score <- score-y)
  
  msoa_max_type <- max(msoa_eval_data_type2$revised_score)
  msoa_eval_data_type2 <- subset(msoa_eval_data_type2, select=-c(y))
  
  msoa_eval_data_type3 <- merge(msoa_eval_data_type2, msoa_max_type)
  msoa_eval_data_type3 <- within(msoa_eval_data_type3, normalized_score <- 100*(revised_score/y))
  
  msoa_data <- subset(UK_Demographic_Data_Master, select=c(LSOA_Code, LSOA_Name))
  msoa_data <- unique.data.frame(msoa_data)
  
  msoa_eval_data_type4 <- merge(msoa_eval_data_type3, msoa_data, by.x = ("LSOA_Code"), by.y = c("LSOA_Code"))
  
  msoa_eval_data_type5 <- msoa_eval_data_type4 %>%  mutate(good_ranks = order(order(abs(score), decreasing=TRUE)))
  
  msoa_eval_data_type6 <- merge(msoa_eval_data_type5, resto_types)
  
  
  msoa_eval_data_type_final_price_type <- rbind(msoa_eval_data_type_final_price_type, msoa_eval_data_type6)
  
}

#Now need to merge these 4 files (restaurant, type, price, price-type) into 1 file

#Need to Calculate saturation as well.
msoa_eval_data_type_final_price_type <- unique(msoa_eval_data_type_final_price_type)
#msoa_eval_data_type_final_price_type <- msoa_eval_data_type6
#rm(msoa_eval_data_type_final_price_type)

#rm(msoa_eval_data_type_final)
#msoa_eval_data_type_final <- msoa_eval_data_type6

write.csv(msoa_eval_data_type_final_price_type, "output by type and price")

msoa_eval_data_type_final_price <- distinct(msoa_eval_data_type_final_price)
msoa_eval_data_type_final <- distinct(msoa_eval_data_type_final)
msoa_eval_data_type_final_price_type <- distinct(msoa_eval_data_type_final_price_type)



msoa_eval_data_type_final <- msoa_eval_data_type_final %>% rename( Score_type = normalized_score)
msoa_eval_data_type_final <- msoa_eval_data_type_final %>% rename( Ranking_type = good_ranks)
msoa_eval_data_type_final <- subset(msoa_eval_data_type_final, select = -c(score, revised_score, y))
msoa_eval_data_type_final_price <- msoa_eval_data_type_final_price %>% rename( Score_price = normalized_score)
msoa_eval_data_type_final_price <- msoa_eval_data_type_final_price %>% rename( Ranking_price = good_ranks)
msoa_eval_data_type_final_price <- subset(msoa_eval_data_type_final_price, select = -c(score, revised_score, y))

msoa_eval_data_type_final_price_type <- msoa_eval_data_type_final_price_type %>% rename( Score_price_type = normalized_score)
msoa_eval_data_type_final_price_type <- msoa_eval_data_type_final_price_type %>% rename( Rank_price_type = good_ranks)
msoa_eval_data_type_final_price_type <- subset(msoa_eval_data_type_final_price_type, select = -c(score, revised_score, y))

msoa_data_final_a <- merge(msoa_eval_data_type_final, msoa_eval_data_type_final_price, by="LSOA_Name", all.x=TRUE)
msoa_data_final_a <- distinct(msoa_data_final_a)

msoa_data_final <- merge(msoa_data_final_a, msoa_eval_data_type_final_price_type, by=c("LSOA_Name", "category_alias", "price"), all.x=TRUE)
write.csv(msoa_data_final, "output for Tableau")

###



library(dplyr)
msoa_data_final1 <- subset(msoa_data_final, select = c(category_alias, LSOA_Name, Score_type))
msoa_data_final1 <- distinct(msoa_data_final1)                           
msoa_data_final1 <- msoa_data_final1 %>%
  group_by(category_alias) %>% 
  mutate(percentrank_type = ntile(Score_type,100))

restos_london_scores <- merge(berlin_restos1b, msoa_data_final1, by.x=c("category_alias", "LSOA_Name"), by.y=c("category_alias", "LSOA_Name"), all.x=TRUE)
restos_london_scores <- distinct(restos_london_scores)

msoa_data_final2 <- subset(msoa_data_final, select = c(category_alias, price, LSOA_Name, Score_price_type))
msoa_data_final2 <- distinct(msoa_data_final2)                           
msoa_data_final2 <- msoa_data_final2 %>%
  group_by(category_alias, price) %>% 
  mutate(percentrank_type_price = ntile(Score_price_type,100), na.rm = TRUE,)

restos_london_scores1 <- merge(restos_london_scores, msoa_data_final2, by.x=c("category_alias", "price", "LSOA_Name"), by.y=c("category_alias", "price", "LSOA_Name"), all.x=TRUE)
write.csv(restos_london_scores1, "Restos with Scores")
msoa_eval_data_type_final_price_type <- subset(msoa_eval_data_type_final_price_type, select = -c(score, revised_score, y))

msoa_data_final_a <- merge(msoa_eval_data_type_final, msoa_eval_data_type_final_price, by="LSOA_Name", all.x=TRUE)
msoa_data_final_a <- distinct(msoa_data_final_a)

msoa_data_final <- merge(msoa_data_final_a, msoa_eval_data_type_final_price_type, by=c("LSOA_Name", "category_alias", "price"), all.x=TRUE)
write.csv(msoa_data_final, "output for Tableau")

###



library(dplyr)
msoa_data_final1 <- subset(msoa_data_final, select = c(category_alias, LSOA_Name, Score_type))
msoa_data_final1 <- distinct(msoa_data_final1)                           
msoa_data_final1 <- msoa_data_final1 %>%
  group_by(category_alias) %>% 
  mutate(percentrank_type = ntile(Score_type,100))

restos_london_scores <- merge(berlin_restos1b, msoa_data_final1, by.x=c("category_alias", "LSOA_Name"), by.y=c("category_alias", "LSOA_Name"), all.x=TRUE)
restos_london_scores <- distinct(restos_london_scores)

msoa_data_final2 <- subset(msoa_data_final, select = c(category_alias, price, LSOA_Name, Score_price_type))
msoa_data_final2 <- distinct(msoa_data_final2)                           
msoa_data_final2 <- msoa_data_final2 %>%
  group_by(category_alias, price) %>% 
  mutate(percentrank_type_price = ntile(Score_price_type,100), na.rm = TRUE,)

restos_london_scores1 <- merge(restos_london_scores, msoa_data_final2, by.x=c("category_alias", "price", "LSOA_Name"), by.y=c("category_alias", "price", "LSOA_Name"), all.x=TRUE)
write.csv(restos_london_scores1, "Restos with Scores")
msoa_eval_data_type_final_price_type <- subset(msoa_eval_data_type_final_price_type, select = -c(score, revised_score, y))

msoa_data_final_a <- merge(msoa_eval_data_type_final, msoa_eval_data_type_final_price, by="LSOA_Name", all.x=TRUE)
msoa_data_final_a <- distinct(msoa_data_final_a)

msoa_data_final <- merge(msoa_data_final_a, msoa_eval_data_type_final_price_type, by=c("LSOA_Name", "category_alias", "price"), all.x=TRUE)
write.csv(msoa_data_final, "output for Tableau")

###



library(dplyr)
msoa_data_final1 <- subset(msoa_data_final, select = c(category_alias, LSOA_Name, Score_type))
msoa_data_final1 <- distinct(msoa_data_final1)                           
msoa_data_final1 <- msoa_data_final1 %>%
  group_by(category_alias) %>% 
  mutate(percentrank_type = ntile(Score_type,100))

restos_london_scores <- merge(berlin_restos1b, msoa_data_final1, by.x=c("category_alias", "LSOA_Name"), by.y=c("category_alias", "LSOA_Name"), all.x=TRUE)
restos_london_scores <- distinct(restos_london_scores)

msoa_data_final2 <- subset(msoa_data_final, select = c(category_alias, price, LSOA_Name, Score_price_type))
msoa_data_final2 <- distinct(msoa_data_final2)                           
msoa_data_final2 <- msoa_data_final2 %>%
  group_by(category_alias, price) %>% 
  mutate(percentrank_type_price = ntile(Score_price_type,100), na.rm = TRUE,)

restos_london_scores1 <- merge(restos_london_scores, msoa_data_final2, by.x=c("category_alias", "price", "LSOA_Name"), by.y=c("category_alias", "price", "LSOA_Name"), all.x=TRUE)
write.csv(restos_london_scores1, "Restos with Scores")


msoa_eval_data_3 <- subset(msoa_eval_data, clusterNum==3)
msoa_eval_data_3a <- subset(msoa_eval_data_3, select = c(clusterNum, MSOA_Code, avgWaterTxp,
                                                         avgRealtor,
                                                         avgOffice,
                                                         avgConstruction,
                                                         avgResto,
                                                         avgSportsAct,
                                                         avgHQ,
                                                         avgRentLease,
                                                         avgTravelTour,
                                                         avgSecurity,
                                                         avgOther,
                                                         avgElectricity,
                                                         avgFinAct,
                                                         avgFinAuxAct,
                                                         avgHHS,
                                                         avgRepairHH,
                                                         avgAccomodation,
                                                         avgmining,
                                                         avgWarehouse,
                                                         avgRD,
                                                         avgBlack,
                                                         avgpct_AGE_T0509,
                                                         avgdensit,
                                                         avgclusterWaterTxp,
                                                         avgclusterRealtor,
                                                         avgclusterOffice,
                                                         avgclusterConstruction,
                                                         avgclusterResto,
                                                         avgclusterSportsAct,
                                                         avgclusterHQ,
                                                         avgclusterRentLease,
                                                         avgclusterTravelTour,
                                                         avgclusterSecurity,
                                                         avgclusterOther,
                                                         avgclusterElectricity,
                                                         avgclusterFinAct,
                                                         avgclusterFinAuxAct,
                                                         avgclusterHHS,
                                                         avgclusterRepairHH,
                                                         avgclusterAccomodation,
                                                         avgclustermining,
                                                         avgclusterWarehouse,
                                                         avgclusterRD,
                                                         avgclusterBlack,
                                                         avgclusterpct_AGE_T0509,
                                                         avgclusterdensit))

msoa_eval_data_3a <- within(msoa_eval_data_3a, realtordif <- (avgRealtor - avgclusterRealtor))
msoa_eval_data_3a <- within(msoa_eval_data_3a, watertxpdif <- (avgWaterTxp - avgclusterWaterTxp))
msoa_eval_data_3a <- within(msoa_eval_data_3a, officedif <- avgOffice - avgclusterOffice)
msoa_eval_data_3a <- within(msoa_eval_data_3a, constructiondif <- avgConstruction - avgclusterConstruction)
msoa_eval_data_3a <- within(msoa_eval_data_3a, restodif <- avgResto - avgclusterResto)
msoa_eval_data_3a <- within(msoa_eval_data_3a, sportsdif <- avgSportsAct - avgclusterSportsAct)
msoa_eval_data_3a <- within(msoa_eval_data_3a, hqdif <- avgHQ - avgclusterHQ)
msoa_eval_data_3a <- within(msoa_eval_data_3a, lentleasedif <- avgRentLease - avgclusterRentLease)
msoa_eval_data_3a <- within(msoa_eval_data_3a, traveltourdif <- avgTravelTour - avgclusterTravelTour)
msoa_eval_data_3a <- within(msoa_eval_data_3a, securitydif <- avgSecurity - avgclusterSecurity)
msoa_eval_data_3a <- within(msoa_eval_data_3a, otherdif <- avgOther - avgclusterOther)
msoa_eval_data_3a <- within(msoa_eval_data_3a, electricitydif <- avgElectricity - avgclusterElectricity)
msoa_eval_data_3a <- within(msoa_eval_data_3a, finactdif <- avgFinAct - avgclusterFinAct)
msoa_eval_data_3a <- within(msoa_eval_data_3a, finauxactdif <- avgFinAuxAct - avgclusterFinAuxAct)
msoa_eval_data_3a <- within(msoa_eval_data_3a, hhsdif <- avgHHS - avgclusterHHS)
msoa_eval_data_3a <- within(msoa_eval_data_3a, repairhhdif <- avgRepairHH - avgclusterRepairHH)
msoa_eval_data_3a <- within(msoa_eval_data_3a, accomodationdif <- avgAccomodation - avgclusterAccomodation)
msoa_eval_data_3a <- within(msoa_eval_data_3a, miningdif <- avgmining - avgclustermining)
msoa_eval_data_3a <- within(msoa_eval_data_3a, warehousedif <- avgWarehouse - avgclusterWarehouse)
msoa_eval_data_3a <- within(msoa_eval_data_3a, rddif <- avgRD - avgclusterRD)
msoa_eval_data_3a <- within(msoa_eval_data_3a, blackdif <- avgBlack - avgclusterBlack)
msoa_eval_data_3a <- within(msoa_eval_data_3a, pct_AGE_T0509dif <- avgpct_AGE_T0509 - avgclusterpct_AGE_T0509)
msoa_eval_data_3a <- within(msoa_eval_data_3a, densitdif <- avgdensit - avgclusterdensit)

write.csv(msoa_eval_data_3a, file="msoa3 eval", row.names=TRUE, col.names=TRUE)


msoa_eval_data_5 <- subset(msoa_eval_data, clusterNum==5)
msoa_eval_data_5a <- subset(msoa_eval_data_5, select = c(clusterNum, MSOA_Code, 
                                                         avgRetail,
                                                         avgEducation,
                                                         avgLegal,
                                                         avgTravelTour,
                                                         avgLandscape,
                                                         avgClubs,
                                                         avgRepairHH,
                                                         avgRepairMach,
                                                         avgResto,
                                                         avgRentLease,
                                                         avgHHS,
                                                         avgChemMan,
                                                         avgManCars,
                                                         avgManOtherTrans,
                                                         avgOther,
                                                         avgCasino,
                                                         avgPost,
                                                         avgConstruction,
                                                         avgclusterRetail,
                                                         avgclusterEducation,
                                                         avgclusterLegal,
                                                         avgclusterTravelTour,
                                                         avgclusterLandscape,
                                                         avgclusterClubs,
                                                         avgclusterRepairHH,
                                                         avgclusterRepairMach,
                                                         avgclusterResto,
                                                         avgclusterRentLease,
                                                         avgclusterHHS,
                                                         avgclusterChemMan,
                                                         avgclusterManOtherTrans,
                                                         avgclusterOther,
                                                         avgclusterPost,
                                                         avgclusterConstruction))

write.csv(msoa_eval_data_5a, file="msoa eval 5", row.names=TRUE, col.names=TRUE)


msoa_eval_data_6 <- subset(msoa_eval_data, clusterNum==6)
msoa_eval_data_6a <- subset(msoa_eval_data_6, select = c(clusterNum, MSOA_Code, 
                                                         avgpct_AGE_T2024,
                                                         avgOther_Other,
                                                         avgRetail,
                                                         avg0125mile,
                                                         avgPharmaMan,
                                                         avgTV,
                                                         avgWholesaleRetail,
                                                         avg025mile,
                                                         avgMovieProd,
                                                         avgCasino,
                                                         avgFurnMan,
                                                         avgOther_Asian,
                                                         avgpct_AGE_T2529,
                                                         avgAsian_Chinese,
                                                         avgResto,
                                                         avgEducation,
                                                         avgOther_Arab,        
                                                         avgclusterpct_AGE_T2024,
                                                         avgclusterOther_Other,
                                                         avgclusterRetail,
                                                         avgcluster0125mile,
                                                         avgclusterPharmaMan,
                                                         avgclusterTV,
                                                         avgclusterWholesaleRetail,
                                                         avgcluster025mile,
                                                         avgclusterMovieProd,
                                                         avgclusterCasino,
                                                         avgclusterFurnMan,
                                                         avgclusterOther_Asian,
                                                         avgclusterpct_AGE_T2529,
                                                         avgclusterAsian_Chinese,
                                                         avgclusterResto,
                                                         avgclusterEducation,
                                                         avgclusterOther_Arab))

write.csv(msoa_eval_data_6a, file="msoa eval 6", row.names=TRUE, col.names=TRUE)

msoa_eval_data_8 <- subset(msoa_eval_data, clusterNum==8)
msoa_eval_data_8a <- subset(msoa_eval_data_8, select = c(clusterNum, MSOA_Code, 
                                                         avgForestry,
                                                         avgOil,
                                                         avgManTextile,
                                                         avgManLeather,
                                                         avgPharmaMan,
                                                         avgManBasicMetal,
                                                         avgElectricalEquip,
                                                         avgWaterTxp,
                                                         avgFinAct,
                                                         avgFinAuxAct,
                                                         avgLegal,
                                                         avgArts,
                                                         avgElectricity,
                                                         avgConstruction,
                                                         avgRealtor,
                                                         avgHQ,
                                                         avgEmployAct,
                                                         avgWholesale,
                                                         avgResto,
                                                         avgMovieProd,
                                                         avgIMD_Decile,
                                                         avgclusterForestry,
                                                         avgclusterOil,
                                                         avgclusterManTextile,
                                                         avgclusterManLeather,
                                                         avgclusterPharmaMan,
                                                         avgclusterManBasicMetal,
                                                         avgclusterElectricalEquip,
                                                         avgclusterWaterTxp,
                                                         avgclusterFinAct,
                                                         avgclusterFinAuxAct,
                                                         avgclusterLegal,
                                                         avgclusterArts,
                                                         avgclusterElectricity,
                                                         avgclusterConstruction,
                                                         avgclusterRealtor,
                                                         avgclusterHQ,
                                                         avgclusterEmployAct,
                                                         avgclusterWholesale,
                                                         avgclusterResto,
                                                         avgclusterMovieProd,
                                                         avgclusterIMD_Decile))

write.csv(msoa_eval_data_8a, file="msoa eval 8", row.names=TRUE, col.names=TRUE)

msoa_eval_data_10 <- subset(msoa_eval_data, clusterNum==10)
msoa_eval_data_10a <- subset(msoa_eval_data_10, select = c(clusterNum, MSOA_Code, 
                                                           avgAirTxp,  
                                                           avgLibraries,  
                                                           avgCasino,  
                                                           avgLandscape,  
                                                           avgMiningSupport,  
                                                           avgFinAct,  
                                                           avgFinAuxAct,  
                                                           avgInsAct,  
                                                           avgRealtor,  
                                                           avgOther,  
                                                           avgConstruction,  
                                                           avgWaterTxp,  
                                                           avgWholesaleRetail,  
                                                           avgLegal,  
                                                           avgSocWork,  
                                                           avgOtherMan,  
                                                           avgElectricity,  
                                                           avgpct_AGE_T0509,
                                                           avgclusterAirTxp,  
                                                           avgclusterLibraries,  
                                                           avgclusterCasino,  
                                                           avgclusterLandscape,  
                                                           avgclusterMiningSupport,  
                                                           avgclusterFinAct,  
                                                           avgclusterFinAuxAct,  
                                                           avgclusterInsAct,  
                                                           avgclusterRealtor,  
                                                           avgclusterOther,  
                                                           avgclusterConstruction,  
                                                           avgclusterWaterTxp,  
                                                           avgclusterWholesaleRetail,  
                                                           avgclusterLegal,  
                                                           avgclusterSocWork,  
                                                           avgclusterOtherMan,  
                                                           avgclusterElectricity,  
                                                           avgclusterpct_AGE_T0509))

write.csv(msoa_eval_data_10a, file="msoa eval 10", row.names=TRUE, col.names=TRUE)

write.csv(berlin_restos1_overview_zipaa, file="london msoa", row.names=TRUE, col.names=TRUE)






resto_corr <- subset(berlin_restos1_overview_zipaa, select = -c(MSOA_Code, clusterNum, na.rm))

cormatrix_resto <- round(cor(resto_corr),2)
write.table(cormatrix_resto, file="mymatrix_restocor.txt", row.names=TRUE, col.names=TRUE)


resto_corr_type3 <- subset(berlin_restos1_overview_zipaa_type, clusterNum==3)
resto_corr_type5 <- subset(berlin_restos1_overview_zipaa_type, clusterNum==5)
resto_corr_type6 <- subset(berlin_restos1_overview_zipaa_type, clusterNum==6)
resto_corr_type8 <- subset(berlin_restos1_overview_zipaa_type, clusterNum==8)
resto_corr_type10 <- subset(berlin_restos1_overview_zipaa_type, clusterNum==10)

resto_corr_type3 <- subset(resto_corr_type3, select = -c(`Greater London`, lsoa11cd, clusterNum, na.rm))
resto_corr_type5 <- subset(resto_corr_type5, select = -c(`Greater London`, lsoa11cd, clusterNum, na.rm))
resto_corr_type6 <- subset(resto_corr_type6, select = -c(`Greater London`, lsoa11cd, clusterNum, na.rm))
resto_corr_type8 <- subset(resto_corr_type8, select = -c(`Greater London`, lsoa11cd, clusterNum, na.rm))
resto_corr_type10 <- subset(resto_corr_type10, select = -c(`Greater London`, lsoa11cd, clusterNum, na.rm))

cormatrix_resto_type3 <- round(cor(resto_corr_type3),2)
cormatrix_resto_type5 <- round(cor(resto_corr_type5),2)
cormatrix_resto_type6 <- round(cor(resto_corr_type6),2)
cormatrix_resto_type8 <- round(cor(resto_corr_type8),2)
cormatrix_resto_type10 <- round(cor(resto_corr_type10),2)

write.csv(cormatrix_resto_type3, file="mymatrix_restocor_type3.txt", row.names=TRUE, col.names=TRUE)
write.csv(cormatrix_resto_type5, file="mymatrix_restocor_type5.txt", row.names=TRUE, col.names=TRUE)
write.csv(cormatrix_resto_type6, file="mymatrix_restocor_type6.txt", row.names=TRUE, col.names=TRUE)
write.csv(cormatrix_resto_type8, file="mymatrix_restocor_type8.txt", row.names=TRUE, col.names=TRUE)
write.csv(cormatrix_resto_type10, file="mymatrix_restocor_type10.txt", row.names=TRUE, col.names=TRUE)


