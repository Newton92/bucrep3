# management/commands/import_nace_simple.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import CategoryNaceCode, SubCategoryNaceCode


class Command(BaseCommand):
    help = 'Import NACE codes from hardcoded data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without saving to database',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        
        # Dictionnaire des poids par catégorie
        poids_categories = {
            "01": 0.5,   # Agriculture and Fishing
            "02": 0.5,   # Cattle
            "03": 0.5,   # Meat
            "04": 0.0,   # Agro food industry (vide dans votre liste)
            "05": 0.5,   # Alcoholic beverages
            "06": 0.5,   # Wood
            "07": 0.5,   # Furniture
            "08": 0.5,   # Mineral products
            "09": 1.0,   # Chemical industry
            "10": 1.0,   # Petroleum and hydrocarbons
            "11": 1.0,   # Transformation of plastic and rubber
            "12": 0.5,   # Glass and Ceramic
            "13": 1.0,   # Pharmaceutical industry and Perfumery
            "14": 0.5,   # Metal
            "15": 1.0,   # Manufacture of fabricated metal products
            "16": 0.5,   # Paper
            "17": 0.5,   # Packing
            "18": 0.5,   # Construction materials
            "19": 0.1,   # Construction
            "20": 0.5,   # Textiles
            "21": 0.5,   # Leather
            "22": 0.5,   # Clothing
            "23": 1.0,   # Mechanical Engineering
            "24": 0.2,   # Measure and precision instrument
            "25": 0.2,   # Electric consumer goods and Telecomm
            "26": 0.2,   # Electric domestic appliances
            "27": 0.2,   # Computers and IT Software/Hardware
            "28": 0.2,   # Telecommunication services
            "29": 0.5,   # Motors vehicles and motorcycles
            "30": 0.2,   # Other vehicules
            "31": 0.2,   # Transport
            "32": 0.2,   # Non specialised trade
            "33": 0.2,   # Printing, media and entertainment
            "34": 0.2,   # Community services
            "35": 1.0,   # Financial services
            "36": 0.2,   # Services to entreprises (except financial)
            "37": 0.2,   # Private and households' services
            "38": 0.1,   # Miscellaneous
            "39": 0.1,   # Miscellaneous and Public Administration
        }
        
        # Données structurées directement dans le code
        # Ceci est un exemple avec les premières données
        nace_entries = [
            # Format: (activity_code, activity_name, type_code, nace_code, nace_denomination)
            # ==================== CATÉGORIE 01 ====================
            # Format: (activity_code, activity_name, type_code, nace_code, nace_denomination)
            ("01", "Agriculture and Fishing", "A - Manufacturers", "0100", "Agriculture, hunting and related service activities"),
            ("01", "Agriculture and Fishing", None, "0110", "Growing of crops; market gardening; horticulture"),
            ("01", "Agriculture and Fishing", None, "0111", "Growing of cereals and other crops n.e.c."),
            ("01", "Agriculture and Fishing", None, "0112", "Growing of vegetables, horticultural specialties and nursery products"),
            ("01", "Agriculture and Fishing", None, "0113", "Growing of fruit, nuts, beverage and spice crops"),
            ("01", "Agriculture and Fishing", None, "0150", "Hunting, trapping and game propagation including related service activities"),
            ("01", "Agriculture and Fishing", None, "0500", "Fishing, operation of fish hatcheries and fish farms; service activities incidental to fishing"),
            ("01", "Agriculture and Fishing", None, "0501", "Fishing"),
            ("01", "Agriculture and Fishing", None, "0502", "Operation of fish hatcheries and fish farms"),
            ("01", "Agriculture and Fishing", None, "0503", "Service activities incidental to fishing"),
            ("01", "Agriculture and Fishing", "B - Wholesalers & Agents", "5111", "Agents involved in the sale of agricultural raw materials, live animals, textile raw materials and semi-finished goods"),
            ("01", "Agriculture and Fishing", "B - Wholesalers & Agents", "5120", "Wholesale of agricultural raw materials and live animals"),
            ("01", "Agriculture and Fishing", "B - Wholesalers & Agents", "5121", "Wholesale of grain, seeds and animal feeds"),
            ("01", "Agriculture and Fishing", "B - Wholesalers & Agents", "5122", "Wholesale of flowers and plants"),
            ("01", "Agriculture and Fishing", "B - Wholesalers & Agents", "5125", "Wholesale of unmanufactured tobacco"),
            ("01", "Agriculture and Fishing", "B - Wholesalers & Agents", "5131", "Wholesale of fruit and vegetables"),
            ("01", "Agriculture and Fishing", "C - Retailers", "5221", "Retail sale of fruit and vegetables"),
            ("01", "Agriculture and Fishing", "C - Retailers", "5223", "Retail sale of fish, crustaceans and molluscs"),
            ("01", "Agriculture and Fishing", "D - Services & other", "0140", "Agricultural and animal husbandry service activities, except veterinary activities"),
            ("01", "Agriculture and Fishing", "D - Services & other", "0141", "Agricultural service activities"),

            # ==================== CATÉGORIE 02 ====================
            ("02", "Cattle", "A - Manufacturers", "0120", "Farming of animals"),
            ("02", "Cattle", None, "0121", "Farming of cattle, dairy farming"),
            ("02", "Cattle", None, "0122", "Farming of sheep, goats, horses, asses, mules and hinnies"),
            ("02", "Cattle", None, "0123", "Farming of swine"),
            ("02", "Cattle", None, "0124", "Farming of poultry"),
            ("02", "Cattle", None, "0125", "Other farming of animals"),
            ("02", "Cattle", None, "0130", "Growing of crops combined with farming of animals (mixed farming)"),
            ("02", "Cattle", "B - Wholesalers & Agents", "5123", "Wholesale of live animals"),
            ("02", "Cattle", "D - Services & other", "0142", "Animal husbandry service activities, except veterinary activities"),

            # ==================== CATÉGORIE 03 ====================
            ("03", "Meat", "A - Manufacturers", "1510", "Production, processing and preserving of meat and meat products"),
            ("03", "Meat", None, "1511", "Production and preserving of meat"),
            ("03", "Meat", None, "1512", "Production and preserving of poultry meat"),
            ("03", "Meat", None, "1513", "Production of meat and poultry meat products"),
            ("03", "Meat", "B - Wholesalers & Agents", "5132", "Wholesale of meat and meat products"),
            ("03", "Meat", "C - Retailers", "5222", "Retail sale of meat and meat products"),
            # ... ajoutez toutes les autres entrées ici
            # ==================== CATÉGORIE 04 ====================
            ("04", "Agro food industry", "A - Manufacturers", "1500", "Manufacture of food products and beverages"),
            ("04", "Agro food industry", None, "1520", "Processing and preserving of fish and fish products"),
            ("04", "Agro food industry", None, "1530", "Processing and preserving of fruit and vegetables"),
            ("04", "Agro food industry", None, "1531", "Processing and preserving of potatoes"),
            ("04", "Agro food industry", None, "1532", "Manufacture of fruit and vegetable juice"),
            ("04", "Agro food industry", None, "1533", "Processing and preserving of fruit and vegetables n.e.c."),
            ("04", "Agro food industry", None, "1540", "Manufacture of vegetable and animal oils and fats"),
            ("04", "Agro food industry", None, "1541", "Manufacture of crude oils and fats"),
            ("04", "Agro food industry", None, "1542", "Manufacture of refined oils and fats"),
            ("04", "Agro food industry", None, "1543", "Manufacture of margarine and similar edible fats"),
            ("04", "Agro food industry", None, "1550", "Manufacture of dairy products"),
            ("04", "Agro food industry", None, "1551", "Operation of dairies and cheese making"),
            ("04", "Agro food industry", None, "1552", "Manufacture of ice cream"),
            ("04", "Agro food industry", None, "1560", "Manufacture of grain mill products, starches and starch products"),
            ("04", "Agro food industry", None, "1561", "Manufacture of grain mill products"),
            ("04", "Agro food industry", None, "1562", "Manufacture of starches and starch products"),
            ("04", "Agro food industry", None, "1570", "Manufacture of prepared animal feeds"),
            ("04", "Agro food industry", None, "1571", "Manufacture of prepared feeds for farm animals"),
            ("04", "Agro food industry", None, "1572", "Manufacture of prepared pet foods"),
            ("04", "Agro food industry", None, "1580", "Manufacture of other food products"),
            ("04", "Agro food industry", None, "1581", "Manufacture of bread; manufacture of fresh pastry goods and cakes"),
            ("04", "Agro food industry", None, "1582", "Manufacture of rusks and biscuits; manufacture of preserved pastry goods and cakes"),
            ("04", "Agro food industry", None, "1583", "Manufacture of sugar"),
            ("04", "Agro food industry", None, "1584", "Manufacture of cocoa; chocolate and sugar confectionery"),
            ("04", "Agro food industry", None, "1585", "Manufacture of macaroni, noodles, couscous and similar farinaceous products"),
            ("04", "Agro food industry", None, "1586", "Processing of tea and coffee"),
            ("04", "Agro food industry", None, "1587", "Manufacture of condiments and seasonings"),
            ("04", "Agro food industry", None, "1588", "Manufacture of homogenised food preparations and dietetic food"),
            ("04", "Agro food industry", None, "1589", "Manufacture of other food products n.e.c."),
            ("04", "Agro food industry", None, "1598", "Production of mineral waters and soft drinks"),
            ("04", "Agro food industry", None, "1600", "Manufacture of tobacco products"),
            ("04", "Agro food industry", "B - Wholesalers & Agents", "5117", "Agents involved in the sale of food, beverages and tobacco"),
            ("04", "Agro food industry", "B - Wholesalers & Agents", "5130", "Wholesale of food, beverages and tobacco"),
            ("04", "Agro food industry", "B - Wholesalers & Agents", "5133", "Wholesale of dairy produce, eggs and edible oils and fats"),
            ("04", "Agro food industry", "B - Wholesalers & Agents", "5135", "Wholesale of tobacco products"),
            ("04", "Agro food industry", "B - Wholesalers & Agents", "5136", "Wholesale of sugar and chocolate and sugar confectionery"),
            ("04", "Agro food industry", "B - Wholesalers & Agents", "5137", "Wholesale of coffee, tea, cocoa and spices"),
            ("04", "Agro food industry", "B - Wholesalers & Agents", "5138", "Wholesale of other food including fish, crustaceans and molluscs"),
            ("04", "Agro food industry", "B - Wholesalers & Agents", "5139", "Non-specialized wholesale of food, beverages and tobacco"),
            ("04", "Agro food industry", "C - Retailers", "5220", "Retail sale of food, beverages and tobacco in specialized stores"),
            ("04", "Agro food industry", "C - Retailers", "5224", "Retail sale of bread, cakes, flour confectionery and sugar confectionery"),
            ("04", "Agro food industry", "C - Retailers", "5226", "Retail sale of tobacco products"),
            ("04", "Agro food industry", "C - Retailers", "5227", "Other retail sale of food, beverages and tobacco in specialized stores"),

            # ==================== CATÉGORIE 05 ====================
            ("05", "Alcoholic beverages", "A - Manufacturers", "1590", "Manufacture of beverages"),
            ("05", "Alcoholic beverages", None, "1591", "Manufacture of distilled potable alcoholic beverages"),
            ("05", "Alcoholic beverages", None, "1592", "Production of ethyl alcohol from fermented materials"),
            ("05", "Alcoholic beverages", None, "1593", "Manufacture of wines"),
            ("05", "Alcoholic beverages", None, "1594", "Manufacture of cider and other fruit wines"),
            ("05", "Alcoholic beverages", None, "1595", "Manufacture of other non-distilled fermented beverages"),
            ("05", "Alcoholic beverages", None, "1596", "Manufacture of beer"),
            ("05", "Alcoholic beverages", None, "1597", "Manufacture of malt"),
            ("05", "Alcoholic beverages", "B - Wholesalers & Agents", "5134", "Wholesale of alcoholic and other beverages"),
            ("05", "Alcoholic beverages", "C - Retailers", "5225", "Retail sale of alcoholic and other beverages"),

            # ==================== CATÉGORIE 06 ====================
            ("06", "Wood", "A - Manufacturers", "0200", "Forestry, logging and related service activities"),
            ("06", "Wood", None, "0201", "Forestry and logging"),
            ("06", "Wood", None, "2000", "Manufacture of wood and of products of wood and cork, except furniture; manufacture of articles of straw and plaiting materials"),
            ("06", "Wood", None, "2010", "Sawmilling and planing of wood, impregnation of wood"),
            ("06", "Wood", None, "2020", "Manufacture of veneer sheets; manufacture of plywood, laminboard, particle board, fibre board and other panels and boards"),
            ("06", "Wood", None, "2050", "Manufacture of other products of wood; manufacture of articles of cork, straw and plaiting materials"),
            ("06", "Wood", None, "2051", "Manufacture of other products of wood"),
            ("06", "Wood", None, "2052", "Manufacture of articles of cork, straw and plaiting materials"),
            ("06", "Wood", "D - Services & other", "0202", "Forestry and logging related service activities"),
            
            # ==================== CATÉGORIE 07 ====================
            ("07", "Furniture", "A - Manufacturers", "3600", "Manufacture of furniture; manufacturing n.e.c."),
            ("07", "Furniture", None, "3610", "Manufacture of furniture"),
            ("07", "Furniture", None, "3611", "Manufacture of chairs and seats"),
            ("07", "Furniture", None, "3612", "Manufacture of other office and shop furniture"),
            ("07", "Furniture", None, "3613", "Manufacture of other kitchen furniture"),
            ("07", "Furniture", None, "3614", "Manufacture of other furniture"),
            ("07", "Furniture", None, "3615", "Manufacture of mattresses"),
            ("07", "Furniture", "B - Wholesalers & Agents", "5115", "Agents involved in the sale of furniture, household goods, hardware and ironmongery"),
            ("07", "Furniture", "C - Retailers", "5244", "Retail sale of furniture, lighting equipment and household articles n.e.c."),

            # ==================== CATÉGORIE 08 ====================
            ("08", "Mineral products", "A - Manufacturers", "1000", "Mining of coal and lignite; extraction of peat"),
            ("08", "Mineral products", None, "1010", "Mining and agglomeration of hard coal"),
            ("08", "Mineral products", None, "1020", "Mining and agglomeration of lignite"),
            ("08", "Mineral products", None, "1030", "Extraction and agglomeration of peat"),
            ("08", "Mineral products", None, "1200", "Mining of uranium and thorium ores"),
            ("08", "Mineral products", None, "1300", "Mining of metal ores"),
            ("08", "Mineral products", None, "1310", "Mining of iron ores"),
            ("08", "Mineral products", None, "1320", "Mining of non-ferrous metal ores, except uranium and thorium ores"),
            ("08", "Mineral products", None, "1430", "Mining of chemical and fertilizer minerals"),
            ("08", "Mineral products", None, "1440", "Production of salt"),
            ("08", "Mineral products", None, "1450", "Other mining and quarrying n.e.c."),
            ("08", "Mineral products", None, "2310", "Manufacture of coke oven products"),
            ("08", "Mineral products", None, "2330", "Processing of nuclear fuel"),
            ("08", "Mineral products", None, "2600", "Manufacture of other non-metallic mineral products"),
            ("08", "Mineral products", None, "2680", "Manufacture of other non-metallic mineral products"),
            ("08", "Mineral products", None, "2682", "Manufacture of other non-metallic mineral products n.e.c."),

            # ==================== CATÉGORIE 09 ====================
            ("09", "Chemical industry", "A - Manufacturers", "2400", "Manufacture of chemicals and chemical products"),
            ("09", "Chemical industry", None, "2410", "Manufacture of basic chemicals"),
            ("09", "Chemical industry", None, "2411", "Manufacture of industrial gases"),
            ("09", "Chemical industry", None, "2412", "Manufacture of dyes and pigments"),
            ("09", "Chemical industry", None, "2413", "Manufacture of other inorganic basic chemicals"),
            ("09", "Chemical industry", None, "2414", "Manufacture of other organic basic chemicals"),
            ("09", "Chemical industry", None, "2415", "Manufacture of fertilizers and nitrogen compounds"),
            ("09", "Chemical industry", None, "2416", "Manufacture of plastics in primary forms"),
            ("09", "Chemical industry", None, "2417", "Manufacture of synthetic rubber in primary forms"),
            ("09", "Chemical industry", None, "2420", "Manufacture of pesticides and other agro-chemical products"),
            ("09", "Chemical industry", None, "2430", "Manufacture of paints, varnishes and similar coatings, printing ink and mastics"),
            ("09", "Chemical industry", None, "2450", "Manufacture of soap and detergents, cleaning and polishing preparations, perfumes and toilet preparations"),
            ("09", "Chemical industry", None, "2451", "Manufacture of soap and detergents, cleaning and polishing preparations"),
            ("09", "Chemical industry", None, "2460", "Manufacture of other chemical products"),
            ("09", "Chemical industry", None, "2461", "Manufacture of explosives"),
            ("09", "Chemical industry", None, "2462", "Manufacture of glues and gelatines"),
            ("09", "Chemical industry", None, "2463", "Manufacture of essential oils"),
            ("09", "Chemical industry", None, "2464", "Manufacture of photographic chemical material"),
            ("09", "Chemical industry", None, "2465", "Manufacture of prepared unrecorded media"),
            ("09", "Chemical industry", None, "2466", "Manufacture of other chemical products n.e.c."),
            ("09", "Chemical industry", None, "2521", "Manufacture of plastic plates, sheets, tubes and profiles"),
            ("09", "Chemical industry", None, "2681", "Production of abrasive products"),
            ("09", "Chemical industry", "B - Wholesalers & Agents", "5155", "Wholesale of chemical products"),
            
                        # ==================== CATÉGORIE 10 ====================
            ("10", "Petroleum and hydrocarbons", "A - Manufacturers", "1100", "Extraction of crude petroleum and natural gas; service activities incidental to oil and gas extraction excluding surveying"),
            ("10", "Petroleum and hydrocarbons", None, "1110", "Extraction of crude petroleum and natural gas"),
            ("10", "Petroleum and hydrocarbons", None, "1111", "Extraction of crude petroleum"),
            ("10", "Petroleum and hydrocarbons", None, "1112", "Extraction of natural gas"),
            ("10", "Petroleum and hydrocarbons", None, "2300", "Manufacture of coke, refined petroleum products and nuclear fuel"),
            ("10", "Petroleum and hydrocarbons", None, "2320", "Manufacture of refined petroleum products"),
            ("10", "Petroleum and hydrocarbons", "B - Wholesalers & Agents", "5112", "Agents involved in the sale of fuels, ores, metals and industrial chemicals"),
            ("10", "Petroleum and hydrocarbons", "B - Wholesalers & Agents", "5151", "Wholesale of solid, liquid and gaseous fuels and related products"),
            ("10", "Petroleum and hydrocarbons", "C - Retailers", "5050", "Retail sale of automotive fuel"),
            ("10", "Petroleum and hydrocarbons", "D - Services & other", "1120", "Service activities incidental to oil and gas extraction excluding surveying"),

            # ==================== CATÉGORIE 11 ====================
            ("11", "Transformation of plastic and rubber", "A - Manufacturers", "2500", "Manufacture of rubber and plastic products"),
            ("11", "Transformation of plastic and rubber", None, "2510", "Manufacture of rubber products"),
            ("11", "Transformation of plastic and rubber", None, "2513", "Manufacture of other rubber products"),
            ("11", "Transformation of plastic and rubber", None, "2520", "Manufacture of plastic products"),
            ("11", "Transformation of plastic and rubber", None, "2523", "Manufacture of builders' ware of plastic"),
            ("11", "Transformation of plastic and rubber", None, "2524", "Manufacture of other plastic products"),

            # ==================== CATÉGORIE 12 ====================
            ("12", "Glass and Ceramic", "A - Manufacturers", "2610", "Manufacture of glass and glass products"),
            ("12", "Glass and Ceramic", None, "2611", "Manufacture of flat glass"),
            ("12", "Glass and Ceramic", None, "2612", "Shaping and processing of flat glass"),
            ("12", "Glass and Ceramic", None, "2613", "Manufacture of hollow glass"),
            ("12", "Glass and Ceramic", None, "2614", "Manufacture of glass fibres"),
            ("12", "Glass and Ceramic", None, "2615", "Manufacture and processing of other glass including technical glassware"),
            ("12", "Glass and Ceramic", None, "2620", "Manufacture of non-refractory ceramic goods other than for construction purposes; manufacture of refractory ceramic products"),
            ("12", "Glass and Ceramic", None, "2621", "Manufacture of ceramic household and ornamental articles"),
            ("12", "Glass and Ceramic", None, "2623", "Manufacture of ceramic insulators and insulating fittings"),
            ("12", "Glass and Ceramic", None, "2624", "Manufacture of other technical ceramic products"),
            ("12", "Glass and Ceramic", None, "2625", "Manufacture of other ceramic products"),
            ("12", "Glass and Ceramic", None, "2626", "Manufacture of refractory ceramic products"),
            ("12", "Glass and Ceramic", "B - Wholesalers & Agents", "5144", "Wholesale of china and glassware, wallpaper and cleaning materials"),
            
                        # ==================== CATÉGORIE 13 ====================
            ("13", "Pharmaceutical industry and Perfumery", "A - Manufacturers", "2440", "Manufacture of pharmaceuticals, medicinal chemicals and botanical products"),
            ("13", "Pharmaceutical industry and Perfumery", None, "2441", "Manufacture of basic pharmaceutical products"),
            ("13", "Pharmaceutical industry and Perfumery", None, "2442", "Manufacture of pharmaceutical preparations"),
            ("13", "Pharmaceutical industry and Perfumery", None, "2452", "Manufacture of perfumes and toilet preparations"),
            ("13", "Pharmaceutical industry and Perfumery", "B - Wholesalers & Agents", "5145", "Wholesale of perfume and cosmetics"),
            ("13", "Pharmaceutical industry and Perfumery", "B - Wholesalers & Agents", "5146", "Wholesale of pharmaceutical goods"),
            ("13", "Pharmaceutical industry and Perfumery", "C - Retailers", "5230", "Retail sale of pharmaceutical and medical goods, cosmetic and toilet articles"),
            ("13", "Pharmaceutical industry and Perfumery", "C - Retailers", "5231", "Dispensing chemists"),
            ("13", "Pharmaceutical industry and Perfumery", "C - Retailers", "5233", "Retail sale of cosmetic and toilet articles"),

            # ==================== CATÉGORIE 14 ====================
            ("14", "Metal", "A - Manufacturers", "2700", "Manufacture of basic metals"),
            ("14", "Metal", None, "2710", "Manufacture of basic iron and steel and of ferro-alloys (ECSC)"),
            ("14", "Metal", None, "2720", "Manufacture of tubes"),
            ("14", "Metal", None, "2721", "Manufacture of cast iron tubes"),
            ("14", "Metal", None, "2722", "Manufacture of steel tubes"),
            ("14", "Metal", None, "2730", "Other first processing of iron and steel and production of non-ECSC ferro-alloys"),
            ("14", "Metal", None, "2731", "Cold drawing"),
            ("14", "Metal", None, "2732", "Cold rolling of narrow strips"),
            ("14", "Metal", None, "2733", "Cold forming or folding"),
            ("14", "Metal", None, "2734", "Wire drawing"),
            ("14", "Metal", None, "2735", "Other first processing of iron and steel n.e.c.; production of non-ECSC ferro-alloys"),
            ("14", "Metal", None, "2740", "Manufacture of basic precious and non-ferrous metals"),
            ("14", "Metal", None, "2741", "Precious metals production"),
            ("14", "Metal", None, "2742", "Aluminium production"),
            ("14", "Metal", None, "2743", "Lead, zinc and tin production"),
            ("14", "Metal", None, "2744", "Copper production"),
            ("14", "Metal", None, "2745", "Other non-ferrous metal production"),
            ("14", "Metal", None, "2750", "Casting of metals"),
            ("14", "Metal", None, "2751", "Casting of iron"),
            ("14", "Metal", None, "2752", "Casting of steel"),
            ("14", "Metal", None, "2753", "Casting of light metals"),
            ("14", "Metal", None, "2754", "Casting of other non-ferrous metals"),
            ("14", "Metal", None, "2850", "Treatment and coating of metals; general mechanical engineering"),
            ("14", "Metal", None, "2851", "Treatment and coating of metals"),
            ("14", "Metal", None, "2875", "Manufacture of other fabricated metal products, n.e.c."),
            ("14", "Metal", "B - Wholesalers & Agents", "3710", "Recycling of metal waste and scrap"),
            ("14", "Metal", "B - Wholesalers & Agents", "5152", "Wholesale of metals and metal ores"),

            # ==================== CATÉGORIE 15 ====================
            ("15", "Manufacture of fabricated metal products", "A - Manufacturers", "2800", "Manufacture of fabricated metal products, except machinery and equipment"),
            ("15", "Manufacture of fabricated metal products", None, "2811", "Manufacture of metal structures and parts of structures"),
            ("15", "Manufacture of fabricated metal products", None, "2820", "Manufacture of tanks, reservoirs and containers of metal; manufacture of central heating radiators and boilers"),
            ("15", "Manufacture of fabricated metal products", None, "2821", "Manufacture of tanks, reservoirs and containers of metal"),
            ("15", "Manufacture of fabricated metal products", None, "2822", "Manufacture of central heating radiators and boilers"),
            ("15", "Manufacture of fabricated metal products", None, "2830", "Manufacture of steam generators, except central heating hot water boilers"),
            ("15", "Manufacture of fabricated metal products", None, "2840", "Forging, pressing, stamping and roll forming of metal; powder metallurgy"),
            ("15", "Manufacture of fabricated metal products", None, "2860", "Manufacture of cutlery, tools and general hardware"),
            ("15", "Manufacture of fabricated metal products", None, "2861", "Manufacture of cutlery"),
            ("15", "Manufacture of fabricated metal products", None, "2862", "Manufacture of tools"),
            ("15", "Manufacture of fabricated metal products", None, "2863", "Manufacture of locks and hinges"),
            ("15", "Manufacture of fabricated metal products", None, "2870", "Manufacture of other fabricated metal products"),
            ("15", "Manufacture of fabricated metal products", None, "2871", "Manufacture of steel drums and similar containers"),
            ("15", "Manufacture of fabricated metal products", None, "2873", "Manufacture of wire products"),
            ("15", "Manufacture of fabricated metal products", None, "2874", "Manufacture of fasteners, screw machine products, chain and springs"),
            
                        # ==================== CATÉGORIE 16 ====================
            ("16", "Paper", "A - Manufacturers", "2100", "Manufacture of pulp, paper and paper products"),
            ("16", "Paper", None, "2110", "Manufacture of pulp, paper and paperboard"),
            ("16", "Paper", None, "2111", "Manufacture of pulp"),
            ("16", "Paper", None, "2112", "Manufacture of paper and paperboard"),
            ("16", "Paper", None, "2120", "Manufacture of articles of paper and paperboard"),
            ("16", "Paper", None, "2122", "Manufacture of household and sanitary goods and of toilet requisites"),
            ("16", "Paper", None, "2125", "Manufacture of other articles of paper and paperboard n.e.c."),

            # ==================== CATÉGORIE 17 ====================
            ("17", "Packing", "A - Manufacturers", "2040", "Manufacture of wooden containers"),
            ("17", "Packing", None, "2121", "Manufacture of corrugated paper and paperboard and of containers of paper and paperboard"),
            ("17", "Packing", None, "2522", "Manufacture of plastic packing goods"),
            ("17", "Packing", None, "2872", "Manufacture of light metal packaging"),
            ("17", "Packing", "D - Services & other", "7482", "Packaging activities"),

            # ==================== CATÉGORIE 18 ====================
            ("18", "Construction materials", "A - Manufacturers", "1400", "Other mining and quarrying"),
            ("18", "Construction materials", None, "1410", "Quarrying of stone"),
            ("18", "Construction materials", None, "1411", "Quarrying of stone for construction"),
            ("18", "Construction materials", None, "1412", "Quarrying of limestone, gypsum and chalk"),
            ("18", "Construction materials", None, "1413", "Quarrying of slate"),
            ("18", "Construction materials", None, "1420", "Quarrying of sand and clay"),
            ("18", "Construction materials", None, "1421", "Operation of gravel and sand pits"),
            ("18", "Construction materials", None, "1422", "Mining of clays and kaolin"),
            ("18", "Construction materials", None, "2030", "Manufacture of builders' carpentry and joinery"),
            ("18", "Construction materials", None, "2124", "Manufacture of wallpaper"),
            ("18", "Construction materials", None, "2622", "Manufacture of ceramic sanitary fixtures"),
            ("18", "Construction materials", None, "2630", "Manufacture of ceramic tiles and flags"),
            ("18", "Construction materials", None, "2640", "Manufacture of bricks, tiles and construction products, in baked clay"),
            ("18", "Construction materials", None, "2650", "Manufacture of cement, lime and plaster"),
            ("18", "Construction materials", None, "2651", "Manufacture of cement"),
            ("18", "Construction materials", None, "2652", "Manufacture of lime"),
            ("18", "Construction materials", None, "2653", "Manufacture of plaster"),
            ("18", "Construction materials", None, "2660", "Manufacture of articles of concrete, plaster and cement"),
            ("18", "Construction materials", None, "2661", "Manufacture of concrete products for construction purposes"),
            ("18", "Construction materials", None, "2662", "Manufacture of plaster products for construction purposes"),
            ("18", "Construction materials", None, "2663", "Manufacture of ready-mixed concrete"),
            ("18", "Construction materials", None, "2664", "Manufacture of mortars"),
            ("18", "Construction materials", None, "2665", "Manufacture of fibre cement"),
            ("18", "Construction materials", None, "2666", "Manufacture of other articles of concrete, plaster and cement"),
            ("18", "Construction materials", None, "2670", "Cutting, shaping and finishing of stone"),
            ("18", "Construction materials", None, "2810", "Manufacture of structural metal products"),
            ("18", "Construction materials", None, "2812", "Manufacture of builders' carpentry and joinery of metal"),
            ("18", "Construction materials", "B - Wholesalers & Agents", "5113", "Agents involved in the sale of timber and building materials"),
            ("18", "Construction materials", "B - Wholesalers & Agents", "5153", "Wholesale of wood, construction materials and sanitary equipment"),
            ("18", "Construction materials", "B - Wholesalers & Agents", "5154", "Wholesale of hardware, plumbing and heating equipment and supplies"),
            ("18", "Construction materials", "C - Retailers", "5246", "Retail sale of hardware, paints and glass"),
            
                        # ==================== CATÉGORIE 19 ====================
            ("19", "Construction", "A - Manufacturers", "4500", "Construction"),
            ("19", "Construction", None, "4510", "Site preparation"),
            ("19", "Construction", None, "4511", "Demolition and wrecking of buildings, earth moving"),
            ("19", "Construction", None, "4512", "Test drilling and boring"),
            ("19", "Construction", None, "4520", "Building of complete constructions or parts thereof; civil engineering"),
            ("19", "Construction", None, "4521", "General construction of buildings and civil engineering works"),
            ("19", "Construction", None, "4522", "Erection of roof covering and frames"),
            ("19", "Construction", None, "4523", "Construction of highways, roads, airfields and sport facilities"),
            ("19", "Construction", None, "4524", "Construction of water projects"),
            ("19", "Construction", None, "4525", "Other construction work involving special trades"),
            ("19", "Construction", None, "4530", "Building installation"),
            ("19", "Construction", None, "4531", "Installation of electrical wiring and fittings"),
            ("19", "Construction", None, "4532", "Insulation work activities"),
            ("19", "Construction", None, "4533", "Plumbing"),
            ("19", "Construction", None, "4534", "Other building installation"),
            ("19", "Construction", None, "4540", "Building completion"),
            ("19", "Construction", None, "4541", "Plastering"),
            ("19", "Construction", None, "4542", "Joinery installation"),
            ("19", "Construction", None, "4543", "Floor and wall covering"),
            ("19", "Construction", None, "4544", "Painting and glazing"),
            ("19", "Construction", None, "4545", "Other building completion"),
            ("19", "Construction", "D - Services & other", "4550", "Renting of construction or demolition equipment with operator"),
            ("19", "Construction", "D - Services & other", "7000", "Real estate activities"),
            ("19", "Construction", "D - Services & other", "7010", "Real estate activities with own property"),
            ("19", "Construction", "D - Services & other", "7011", "Development and selling of real estate"),
            ("19", "Construction", "D - Services & other", "7012", "Buying and selling of own real estate"),
            ("19", "Construction", "D - Services & other", "7020", "Letting of own property"),
            ("19", "Construction", "D - Services & other", "7030", "Real estate activities on a fee or contract basis"),
            ("19", "Construction", "D - Services & other", "7031", "Real estate agencies"),
            ("19", "Construction", "D - Services & other", "7032", "Management of real estate on a fee or contract basis"),
            ("19", "Construction", "D - Services & other", "7132", "Renting of construction and civil engineering machinery and equipment"),
            ("19", "Construction", "D - Services & other", "7420", "Architectural and engineering activities and related technical consultancy"),

            # ==================== CATÉGORIE 20 ====================
            ("20", "Textiles", "A - Manufacturers", "1700", "Manufacture of textiles"),
            ("20", "Textiles", None, "1710", "Preparation and spinning of textile fibres"),
            ("20", "Textiles", None, "1711", "Preparation and spinning of cotton-type fibres"),
            ("20", "Textiles", None, "1712", "Preparation and spinning of woollen-type fibres"),
            ("20", "Textiles", None, "1713", "Preparation and spinning of worsted-type fibres"),
            ("20", "Textiles", None, "1714", "Preparation and spinning of flax-type fibres"),
            ("20", "Textiles", None, "1715", "Throwing and preparation of silk including from noils and throwing and texturing of synthetic or artificial filament yarns"),
            ("20", "Textiles", None, "1716", "Manufacture of sewing threads"),
            ("20", "Textiles", None, "1717", "Preparation and spinning of other textile fibres"),
            ("20", "Textiles", None, "1720", "Textile weaving"),
            ("20", "Textiles", None, "1721", "Cotton-type weaving"),
            ("20", "Textiles", None, "1722", "Woollen-type weaving"),
            ("20", "Textiles", None, "1723", "Worsted-type weaving"),
            ("20", "Textiles", None, "1724", "Silk-type weaving"),
            ("20", "Textiles", None, "1725", "Other textile weaving"),
            ("20", "Textiles", None, "1730", "Finishing of textiles"),
            ("20", "Textiles", None, "1750", "Manufacture of other textiles"),
            ("20", "Textiles", None, "1751", "Manufacture of carpets and rugs"),
            ("20", "Textiles", None, "1752", "Manufacture of cordage, rope, twine and netting"),
            ("20", "Textiles", None, "1753", "Manufacture of nonwovens and articles made from nonwovens, except apparel"),
            ("20", "Textiles", None, "2470", "Manufacture of man-made fibres"),
            ("20", "Textiles", "B - Wholesalers & Agents", "5141", "Wholesale of textiles"),
            ("20", "Textiles", "C - Retailers", "5241", "Retail sale of textiles"),

            # ==================== CATÉGORIE 21 ====================
            ("21", "Leather", "A - Manufacturers", "1900", "Tanning and dressing of leather; manufacture of luggage, handbags, saddlery, harness and footwear"),
            ("21", "Leather", None, "1910", "Tanning and dressing of leather"),
            ("21", "Leather", None, "1920", "Manufacture of luggage, handbags and the like, saddlery and harness"),
            ("21", "Leather", "B - Wholesalers & Agents", "5124", "Wholesale of hides, skins and leather"),
            
                        # ==================== CATÉGORIE 22 ====================
            ("22", "Clothing", "A - Manufacturers", "1740", "Manufacture of made-up textile articles, except apparel"),
            ("22", "Clothing", None, "1754", "Manufacture of other textiles n.e.c."),
            ("22", "Clothing", None, "1760", "Manufacture of knitted and crocheted fabrics"),
            ("22", "Clothing", None, "1770", "Manufacture of knitted and crocheted articles"),
            ("22", "Clothing", None, "1771", "Manufacture of knitted and crocheted hosiery"),
            ("22", "Clothing", None, "1772", "Manufacture of knitted and crocheted pullovers, cardigans and similar articles"),
            ("22", "Clothing", None, "1800", "Manufacture of wearing apparel; dressing and dyeing of fur"),
            ("22", "Clothing", None, "1810", "Manufacture of leather clothes"),
            ("22", "Clothing", None, "1820", "Manufacture of other wearing apparel and accessories"),
            ("22", "Clothing", None, "1821", "Manufacture of workwear"),
            ("22", "Clothing", None, "1822", "Manufacture of other outerwear"),
            ("22", "Clothing", None, "1823", "Manufacture of underwear"),
            ("22", "Clothing", None, "1824", "Manufacture of other wearing apparel and accessories n.e.c."),
            ("22", "Clothing", None, "1830", "Dressing and dyeing of fur; manufacture of articles of fur"),
            ("22", "Clothing", None, "1930", "Manufacture of footwear"),
            ("22", "Clothing", "B - Wholesalers & Agents", "5116", "Agents involved in the sale of textiles, clothing, footwear and leather goods"),
            ("22", "Clothing", "B - Wholesalers & Agents", "5142", "Wholesale of clothing and footwear"),
            ("22", "Clothing", "C - Retailers", "5242", "Retail sale of clothing"),
            ("22", "Clothing", "C - Retailers", "5243", "Retail sale of footwear and leather goods"),

            # ==================== CATÉGORIE 23 ====================
            ("23", "Mechanical Engineering", "A - Manufacturers", "2900", "Manufacture of machinery and equipment n.e.c."),
            ("23", "Mechanical Engineering", None, "2910", "Manufacture of machinery for the production and use of mechanical power, except aircraft, vehicle and cycle engines"),
            ("23", "Mechanical Engineering", None, "2911", "Manufacture of engines and turbines, except aircraft, vehicle and cycle engines"),
            ("23", "Mechanical Engineering", None, "2912", "Manufacture of pumps and compressors"),
            ("23", "Mechanical Engineering", None, "2913", "Manufacture of taps and valves"),
            ("23", "Mechanical Engineering", None, "2914", "Manufacture of bearings, gears, gearing and driving elements"),
            ("23", "Mechanical Engineering", None, "2920", "Manufacture of other general purpose machinery"),
            ("23", "Mechanical Engineering", None, "2921", "Manufacture of furnaces and furnace burners"),
            ("23", "Mechanical Engineering", None, "2922", "Manufacture of lifting and handling equipment"),
            ("23", "Mechanical Engineering", None, "2923", "Manufacture of non-domestic cooling and ventilation equipment"),
            ("23", "Mechanical Engineering", None, "2924", "Manufacture of other general purpose machinery n.e.c."),
            ("23", "Mechanical Engineering", None, "2930", "Manufacture of agricultural and forestry machinery"),
            ("23", "Mechanical Engineering", None, "2931", "Manufacture of agricultural tractors"),
            ("23", "Mechanical Engineering", None, "2932", "Manufacture of other agricultural and forestry machinery"),
            ("23", "Mechanical Engineering", None, "2940", "Manufacture of machine-tools"),
            ("23", "Mechanical Engineering", None, "2950", "Manufacture of other special purpose machinery"),
            ("23", "Mechanical Engineering", None, "2951", "Manufacture of machinery for metallurgy"),
            ("23", "Mechanical Engineering", None, "2952", "Manufacture of machinery for mining, quarrying and construction"),
            ("23", "Mechanical Engineering", None, "2953", "Manufacture of machinery for food, beverage and tobacco processing"),
            ("23", "Mechanical Engineering", None, "2954", "Manufacture of machinery for textile, apparel and leather production"),
            ("23", "Mechanical Engineering", None, "2955", "Manufacture of machinery for paper and paperboard production"),
            ("23", "Mechanical Engineering", None, "2956", "Manufacture of other special purpose machinery n.e.c."),
            ("23", "Mechanical Engineering", "B - Wholesalers & Agents", "5114", "Agents involved in the sale of machinery, industrial equipment, ships and aircraft"),
            ("23", "Mechanical Engineering", "B - Wholesalers & Agents", "5160", "Wholesale of machinery, equipment and supplies"),
            ("23", "Mechanical Engineering", "B - Wholesalers & Agents", "5161", "Wholesale of machine tools"),
            ("23", "Mechanical Engineering", "B - Wholesalers & Agents", "5162", "Wholesale of construction machinery"),
            ("23", "Mechanical Engineering", "B - Wholesalers & Agents", "5163", "Wholesale of machinery for the textile industry, and of sewing and knitting machines"),
            ("23", "Mechanical Engineering", "B - Wholesalers & Agents", "5165", "Wholesale of other machinery for use in industry, trade and navigation"),
            ("23", "Mechanical Engineering", "B - Wholesalers & Agents", "5166", "Wholesale of agricultural machinery and accessories and implements, including tractors"),
            ("23", "Mechanical Engineering", "D - Services & other", "2852", "General mechanical engineering"),
            ("23", "Mechanical Engineering", "D - Services & other", "7100", "Renting of machinery and equipment without operator and of personal and household goods"),
            ("23", "Mechanical Engineering", "D - Services & other", "7130", "Renting of other machinery and equipment"),
            ("23", "Mechanical Engineering", "D - Services & other", "7131", "Renting of agricultural machinery and equipment"),
            ("23", "Mechanical Engineering", "D - Services & other", "7134", "Renting of other machinery and equipment n.e.c."),

            # ==================== CATÉGORIE 24 ====================
            ("24", "Measure and precision instrument", "A - Manufacturers", "2960", "Manufacture of weapons and ammunition"),
            ("24", "Measure and precision instrument", None, "3300", "Manufacture of medical, precision and optical instruments, watches and clocks"),
            ("24", "Measure and precision instrument", None, "3310", "Manufacture of medical and surgical equipment and orthopaedic appliances"),
            ("24", "Measure and precision instrument", None, "3320", "Manufacture of instruments and appliances for measuring, checking, testing, navigating and other purposes, except industrial process control equipment"),
            ("24", "Measure and precision instrument", None, "3330", "Manufacture of industrial process control equipment"),
            ("24", "Measure and precision instrument", None, "3340", "Manufacture of optical instruments and photographic equipment"),
            ("24", "Measure and precision instrument", None, "3350", "Manufacture of watches and clocks"),
            ("24", "Measure and precision instrument", "C - Retailers", "5232", "Retail sale of medical and orthopaedic goods"),
            ("24", "Measure and precision instrument", "D - Services & other", "7300", "Research and development"),
            ("24", "Measure and precision instrument", "D - Services & other", "7310", "Research and experimental development on natural sciences and engineering"),
            ("24", "Measure and precision instrument", "D - Services & other", "7320", "Research and experimental development on social sciences and humanities"),
            ("24", "Measure and precision instrument", "D - Services & other", "7430", "Technical testing and analysis"),
            
                        # ==================== CATÉGORIE 25 ====================
            ("25", "Electric consumer goods and Telecomm", "A - Manufacturers", "3100", "Manufacture of electrical machinery and apparatus n.e.c."),
            ("25", "Electric consumer goods and Telecomm", None, "3110", "Manufacture of electric motors, generators and transformers"),
            ("25", "Electric consumer goods and Telecomm", None, "3120", "Manufacture of electricity distribution and control apparatus"),
            ("25", "Electric consumer goods and Telecomm", None, "3130", "Manufacture of insulated wire and cable"),
            ("25", "Electric consumer goods and Telecomm", None, "3140", "Manufacture of accumulators, primary cells and primary batteries"),
            ("25", "Electric consumer goods and Telecomm", None, "3150", "Manufacture of lighting equipment and electric lamps"),
            ("25", "Electric consumer goods and Telecomm", None, "3160", "Manufacture of electrical equipment n.e.c."),
            ("25", "Electric consumer goods and Telecomm", None, "3161", "Manufacture of electrical equipment for engines and vehicles n.e.c."),
            ("25", "Electric consumer goods and Telecomm", None, "3162", "Manufacture of other electrical equipment n.e.c."),
            ("25", "Electric consumer goods and Telecomm", None, "3210", "Manufacture of electronic valves and tubes and other electronic components"),
            ("25", "Electric consumer goods and Telecomm", None, "3220", "Manufacture of television and radio transmitters and apparatus for line telephony and line telegraphy"),

            # ==================== CATÉGORIE 26 ====================
            ("26", "Electric domestic appliances", "A - Manufacturers", "2970", "Manufacture of domestic appliances n.e.c."),
            ("26", "Electric domestic appliances", None, "2971", "Manufacture of electric domestic appliances"),
            ("26", "Electric domestic appliances", None, "2972", "Manufacture of non-electric domestic appliances"),
            ("26", "Electric domestic appliances", None, "3200", "Manufacture of radio, television and communication equipment and apparatus"),
            ("26", "Electric domestic appliances", None, "3230", "Manufacture of television and radio receivers, sound or video recording or reproducing apparatus and associated goods"),
            ("26", "Electric domestic appliances", "B - Wholesalers & Agents", "5143", "Wholesale of electrical household appliances and radio and television goods"),
            ("26", "Electric domestic appliances", "C - Retailers", "5245", "Retail sale of electrical household appliances and radio and television goods"),

            # ==================== CATÉGORIE 27 ====================
            ("27", "Computers and IT Software/Hardware", "A - Manufacturers", "3000", "Manufacture of office machinery and computers"),
            ("27", "Computers and IT Software/Hardware", None, "3001", "Manufacture of office machinery"),
            ("27", "Computers and IT Software/Hardware", None, "3002", "Manufacture of computers and other information processing equipment"),
            ("27", "Computers and IT Software/Hardware", "B - Wholesalers & Agents", "5164", "Wholesale of office machinery and equipment"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "2233", "Reproduction of computer media"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "7133", "Renting of office machinery and equipment including computers"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "7200", "Computer and related activities"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "7210", "Hardware consultancy"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "7220", "Software consultancy and supply"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "7230", "Data processing"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "7240", "Data base activities"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "7250", "Maintenance and repair of office, accounting and computing machinery"),
            ("27", "Computers and IT Software/Hardware", "D - Services & other", "7260", "Other computer related activities"),
            
            
                        # ==================== CATÉGORIE 28 ====================
            ("28", "Telecommunication services", "D - Services & other", "6400", "Post and telecommunications"),
            ("28", "Telecommunication services", "D - Services & other", "6410", "Post and courier activities"),
            ("28", "Telecommunication services", "D - Services & other", "6411", "National post activities"),
            ("28", "Telecommunication services", "D - Services & other", "6412", "Courier activities other than national post activities"),
            ("28", "Telecommunication services", "D - Services & other", "6420", "Telecommunications"),

            # ==================== CATÉGORIE 29 ====================
            ("29", "Motors vehicles and motorcycles", "A - Manufacturers", "2511", "Manufacture of rubber tyres and tubes"),
            ("29", "Motors vehicles and motorcycles", None, "2512", "Retreading and rebuilding of rubber tyres"),
            ("29", "Motors vehicles and motorcycles", None, "3400", "Manufacture of motor vehicles, trailers and semi-trailers"),
            ("29", "Motors vehicles and motorcycles", None, "3410", "Manufacture of motor vehicles"),
            ("29", "Motors vehicles and motorcycles", None, "3420", "Manufacture of bodies (coachwork) for motor vehicles; manufacture of trailers and semi-trailers"),
            ("29", "Motors vehicles and motorcycles", None, "3430", "Manufacture of parts and accessories for motor vehicles and their engines"),
            ("29", "Motors vehicles and motorcycles", None, "3540", "Manufacture of motorcycles and bicycles"),
            ("29", "Motors vehicles and motorcycles", None, "3541", "Manufacture of motorcycles"),
            ("29", "Motors vehicles and motorcycles", None, "3542", "Manufacture of bicycles"),
            ("29", "Motors vehicles and motorcycles", "C - Retailers", "5000", "Sale, maintenance and repair of motor vehicles and motorcycles; retail sale of automotive fuel"),
            ("29", "Motors vehicles and motorcycles", "C - Retailers", "5010", "Sale of motor vehicles"),
            ("29", "Motors vehicles and motorcycles", "C - Retailers", "5030", "Sale of motor vehicle parts and accessories"),
            ("29", "Motors vehicles and motorcycles", "C - Retailers", "5040", "Sale, maintenance and repair of motorcycles and related parts and accessories"),
            ("29", "Motors vehicles and motorcycles", "D - Services & other", "5020", "Maintenance and repair of motor vehicles"),

            # ==================== CATÉGORIE 30 ====================
            ("30", "Other vehicles", "A - Manufacturers", "3500", "Manufacture of other transport equipment"),
            ("30", "Other vehicles", None, "3510", "Building and repairing of ships and boats"),
            ("30", "Other vehicles", None, "3511", "Building and repairing of ships"),
            ("30", "Other vehicles", None, "3512", "Building and repairing of pleasure and sporting boats"),
            ("30", "Other vehicles", None, "3520", "Manufacture of railway and tramway locomotives and rolling stock"),
            ("30", "Other vehicles", None, "3530", "Manufacture of aircraft and spacecraft"),
            ("30", "Other vehicles", None, "3543", "Manufacture of invalid carriages"),
            ("30", "Other vehicles", None, "3550", "Manufacture of other transport equipment n.e.c."),
            
            
                        # ==================== CATÉGORIE 31 ====================
            ("31", "Transport", "D - Services & other", "6000", "Land transport; transport via pipelines"),
            ("31", "Transport", "D - Services & other", "6010", "Transport via railways"),
            ("31", "Transport", "D - Services & other", "6020", "Other land transport"),
            ("31", "Transport", "D - Services & other", "6021", "Other scheduled passenger land transport"),
            ("31", "Transport", "D - Services & other", "6022", "Taxi operation"),
            ("31", "Transport", "D - Services & other", "6023", "Other land passenger transport"),
            ("31", "Transport", "D - Services & other", "6024", "Freight transport by road"),
            ("31", "Transport", "D - Services & other", "6030", "Transport via pipelines"),
            ("31", "Transport", "D - Services & other", "6100", "Water transport"),
            ("31", "Transport", "D - Services & other", "6110", "Sea and coastal water transport"),
            ("31", "Transport", "D - Services & other", "6111", "Sea water transport"),
            ("31", "Transport", "D - Services & other", "6112", "Coastal water transport"),
            ("31", "Transport", "D - Services & other", "6120", "Inland water transport"),
            ("31", "Transport", "D - Services & other", "6200", "Air transport"),
            ("31", "Transport", "D - Services & other", "6210", "Scheduled air transport"),
            ("31", "Transport", "D - Services & other", "6220", "Non-scheduled air transport"),
            ("31", "Transport", "D - Services & other", "6230", "Space transport"),
            ("31", "Transport", "D - Services & other", "6300", "Supporting and auxiliary transport activities; activities of travel agencies"),
            ("31", "Transport", "D - Services & other", "6310", "Cargo handling and storage"),
            ("31", "Transport", "D - Services & other", "6311", "Cargo handling"),
            ("31", "Transport", "D - Services & other", "6312", "Storage and warehousing"),
            ("31", "Transport", "D - Services & other", "6320", "Other supporting transport activities"),
            ("31", "Transport", "D - Services & other", "6321", "Other supporting land transport activities"),
            ("31", "Transport", "D - Services & other", "6322", "Other supporting water transport activities"),
            ("31", "Transport", "D - Services & other", "6323", "Other supporting air transport activities"),
            ("31", "Transport", "D - Services & other", "6330", "Activities of travel agencies and tour operators; tourist assistance activities n.e.c."),
            ("31", "Transport", "D - Services & other", "6340", "Activities of other transport agencies"),
            ("31", "Transport", "D - Services & other", "7110", "Renting of automobiles"),
            ("31", "Transport", "D - Services & other", "7120", "Renting of other transport equipment"),
            ("31", "Transport", "D - Services & other", "7121", "Renting of other land transport equipment"),
            ("31", "Transport", "D - Services & other", "7122", "Renting of water transport equipment"),
            ("31", "Transport", "D - Services & other", "7123", "Renting of air transport equipment"),

            # ==================== CATÉGORIE 32 ====================
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5100", "Wholesale trade and commission trade, except of motor vehicles and motorcycles"),
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5110", "Wholesale on a fee or contract basis"),
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5118", "Agents specializing in the sale of particular products or ranges of products n.e.c."),
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5119", "Agents involved in the sale of a variety of goods"),
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5140", "Wholesale of household goods"),
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5147", "Wholesale of other household goods"),
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5150", "Wholesale of non-agricultural intermediate products, waste and scrap"),
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5156", "Wholesale of other intermediate products"),
            ("32", "Non specialised trade", "B - Wholesalers & Agents", "5170", "Other wholesale"),
            ("32", "Non specialised trade", "C - Retailers", "5200", "Retail trade, except of motor vehicles and motorcycles; repair of personal and household goods"),
            ("32", "Non specialised trade", "C - Retailers", "5210", "Retail sale in non-specialized stores"),
            ("32", "Non specialised trade", "C - Retailers", "5211", "Retail sale in non-specialized stores with food, beverages or tobacco predominating"),
            ("32", "Non specialised trade", "C - Retailers", "5212", "Other retail sale in non-specialized stores"),
            ("32", "Non specialised trade", "C - Retailers", "5240", "Other retail sale of new goods in specialized store"),
            ("32", "Non specialised trade", "C - Retailers", "5248", "Other retail sale in specialized stores"),
            ("32", "Non specialised trade", "C - Retailers", "5250", "Retail sale of second-hand goods in stores"),
            ("32", "Non specialised trade", "C - Retailers", "5260", "Retail sale not in stores"),
            ("32", "Non specialised trade", "C - Retailers", "5261", "Retail sale via mail order houses"),
            ("32", "Non specialised trade", "C - Retailers", "5262", "Retail sale via stalls and markets"),
            ("32", "Non specialised trade", "C - Retailers", "5263", "Other non-store retail sale"),

            # ==================== CATÉGORIE 33 ====================
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2123", "Manufacture of paper stationery"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2200", "Publishing, printing and reproduction of recorded media"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2210", "Publishing"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2211", "Publishing of books"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2212", "Publishing of newspapers"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2213", "Publishing of journals and periodicals"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2214", "Publishing of sound recordings"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2215", "Other publishing"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2220", "Printing and service activities related to printing"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2221", "Printing of newspapers"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2222", "Printing n.e.c."),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2223", "Bookbinding and finishing"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2224", "Composition and plate-making"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2225", "Other activities related to printing"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2230", "Reproduction of recorded media"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2231", "Reproduction of sound recording"),
            ("33", "Printing, media and entertainment", "A - Manufacturers", "2232", "Reproduction of video recording"),
            ("33", "Printing, media and entertainment", "C - Retailers", "5247", "Retail sale of books, newspapers and stationery"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9210", "Motion picture and video activities"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9211", "Motion picture and video production"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9212", "Motion picture and video distribution"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9213", "Motion picture projection"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9220", "Radio and television activities"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9230", "Other entertainment activities"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9231", "Artistic and literary creation and interpretation"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9232", "Operation of arts facilities"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9233", "Fair and amusement park activities"),
            ("33", "Printing, media and entertainment", "D - Services & other", "9234", "Other entertainment activities n.e.c."),
            ("33", "Printing, media and entertainment", "D - Services & other", "9240", "News agency activities"),
            
            
                        # ==================== CATÉGORIE 34 ====================
            ("34", "Community services", "A - Manufacturers", "4000", "Electricity, gas, steam and hot water supply"),
            ("34", "Community services", None, "4010", "Production and distribution of electricity"),
            ("34", "Community services", None, "4020", "Manufacture of gas; distribution of gaseous fuels through mains"),
            ("34", "Community services", None, "4030", "Steam and hot water supply"),
            ("34", "Community services", None, "4100", "Collection, purification and distribution of water"),
            ("34", "Community services", "B - Wholesalers & Agents", "5157", "Wholesale of waste and scrap"),
            ("34", "Community services", "D - Services & other", "3700", "Recycling"),
            ("34", "Community services", "D - Services & other", "3720", "Recycling of non-metal waste and scrap"),
            ("34", "Community services", "D - Services & other", "7500", "Public administration and defence; compulsory social security"),
            ("34", "Community services", "D - Services & other", "7510", "Administration of the state and the economic and social policy of the community"),
            ("34", "Community services", "D - Services & other", "7511", "General (overall) public service activities"),
            ("34", "Community services", "D - Services & other", "7512", "Regulation of the activities of agencies that provide health care, education, cultural services and other social services excluding social security"),
            ("34", "Community services", "D - Services & other", "7513", "Regulation of and contribution to more efficient operation of business"),
            ("34", "Community services", "D - Services & other", "7514", "Supporting service activities for the government as a whole"),
            ("34", "Community services", "D - Services & other", "7520", "Provision of services to the community as a whole"),
            ("34", "Community services", "D - Services & other", "7521", "Foreign affairs"),
            ("34", "Community services", "D - Services & other", "7522", "Defence activities"),
            ("34", "Community services", "D - Services & other", "7523", "Justice and judicial activities"),
            ("34", "Community services", "D - Services & other", "7524", "Public security, law and order activities"),
            ("34", "Community services", "D - Services & other", "7525", "Fire service activities"),
            ("34", "Community services", "D - Services & other", "7530", "Compulsory social security activities"),
            ("34", "Community services", "D - Services & other", "8000", "Education"),
            ("34", "Community services", "D - Services & other", "8010", "Primary education"),
            ("34", "Community services", "D - Services & other", "8020", "Secondary education"),
            ("34", "Community services", "D - Services & other", "8021", "General secondary education"),
            ("34", "Community services", "D - Services & other", "8022", "Technical and vocational secondary education"),
            ("34", "Community services", "D - Services & other", "8030", "Higher education"),
            ("34", "Community services", "D - Services & other", "8040", "Adult and other education"),
            ("34", "Community services", "D - Services & other", "8042", "Adult and other education n.e.c."),
            ("34", "Community services", "D - Services & other", "8500", "Health and social work"),
            ("34", "Community services", "D - Services & other", "8510", "Human health activities"),
            ("34", "Community services", "D - Services & other", "8511", "Hospital activities"),
            ("34", "Community services", "D - Services & other", "8512", "Medical practice activities"),
            ("34", "Community services", "D - Services & other", "8513", "Dental practice activities"),
            ("34", "Community services", "D - Services & other", "8514", "Other human health activities"),
            ("34", "Community services", "D - Services & other", "8520", "Veterinary activities"),
            ("34", "Community services", "D - Services & other", "8530", "Social work activities"),
            ("34", "Community services", "D - Services & other", "8531", "Social work activities with accommodation"),
            ("34", "Community services", "D - Services & other", "8532", "Social work activities without accommodation"),
            ("34", "Community services", "D - Services & other", "9000", "Sewage and refuse disposal, sanitation and similar activities"),
            ("34", "Community services", "D - Services & other", "9100", "Activities of membership organization n.e.c."),
            ("34", "Community services", "D - Services & other", "9110", "Activities of business, employers and professional organizations"),
            ("34", "Community services", "D - Services & other", "9111", "Activities of business and employers organizations"),
            ("34", "Community services", "D - Services & other", "9112", "Activities of professional organizations"),
            ("34", "Community services", "D - Services & other", "9120", "Activities of trade unions"),
            ("34", "Community services", "D - Services & other", "9130", "Activities of other membership organizations"),
            ("34", "Community services", "D - Services & other", "9131", "Activities of religious organizations"),
            ("34", "Community services", "D - Services & other", "9132", "Activities of political organizations"),
            ("34", "Community services", "D - Services & other", "9133", "Activities of other membership organizations n.e.c."),
            ("34", "Community services", "D - Services & other", "9200", "Recreational, cultural and sporting activities"),
            ("34", "Community services", "D - Services & other", "9250", "Library, archives, museums and other cultural activities"),
            ("34", "Community services", "D - Services & other", "9251", "Library and archives activities"),
            ("34", "Community services", "D - Services & other", "9252", "Museums activities and preservation of historical sites and buildings"),
            ("34", "Community services", "D - Services & other", "9253", "Botanical and zoological gardens and nature reserves activities"),
            ("34", "Community services", "D - Services & other", "9260", "Sporting activities"),
            ("34", "Community services", "D - Services & other", "9261", "Operation of sports arenas and stadiums"),
            ("34", "Community services", "D - Services & other", "9262", "Other sporting activities"),
            ("34", "Community services", "D - Services & other", "9270", "Other recreational activities"),
            ("34", "Community services", "D - Services & other", "9272", "Other recreational activities n.e.c."),
            ("34", "Community services", "D - Services & other", "9900", "Extra-territorial organizations and bodies"),

            # ==================== CATÉGORIE 35 ====================
            ("35", "Financial services", "D - Services & other", "6500", "Financial intermediation, except insurance and pension funding"),
            ("35", "Financial services", "D - Services & other", "6510", "Monetary intermediation"),
            ("35", "Financial services", "D - Services & other", "6511", "Central banking"),
            ("35", "Financial services", "D - Services & other", "6512", "Other monetary intermediation"),
            ("35", "Financial services", "D - Services & other", "6520", "Other financial intermediation"),
            ("35", "Financial services", "D - Services & other", "6521", "Financial leasing"),
            ("35", "Financial services", "D - Services & other", "6522", "Other credit granting"),
            ("35", "Financial services", "D - Services & other", "6523", "Other financial intermediation n.e.c."),
            ("35", "Financial services", "D - Services & other", "6600", "Insurance and pension funding, except compulsory social security"),
            ("35", "Financial services", "D - Services & other", "6601", "Life insurance"),
            ("35", "Financial services", "D - Services & other", "6602", "Pension funding"),
            ("35", "Financial services", "D - Services & other", "6603", "Non-life insurance"),
            ("35", "Financial services", "D - Services & other", "6700", "Activities auxiliary to financial intermediation"),
            ("35", "Financial services", "D - Services & other", "6710", "Activities auxiliary to financial intermediation, except insurance and pension funding"),
            ("35", "Financial services", "D - Services & other", "6711", "Administration of financial markets"),
            ("35", "Financial services", "D - Services & other", "6712", "Security broking and fund management"),
            ("35", "Financial services", "D - Services & other", "6713", "Activities auxiliary to financial intermediation n.e.c."),
            ("35", "Financial services", "D - Services & other", "6720", "Activities auxiliary to insurance and pension funding"),
            ("35", "Financial services", "D - Services & other", "7415", "Management activities of holding companies"),

            # ==================== CATÉGORIE 36 ====================
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7400", "Other business activities"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7410", "Legal, accounting, book-keeping and auditing activities; tax consultancy; market research and public opinion polling; business and management consultancy; holdings"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7411", "Legal activities"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7412", "Accounting, book-keeping and auditing activities; tax consultancy"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7413", "Market research and public opinion polling"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7414", "Business and management consultancy activities"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7440", "Advertising"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7450", "Labour recruitment and provision of personnel"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7460", "Investigation and security activities"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7470", "Industrial cleaning"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7480", "Miscellaneous business activities n.e.c"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7481", "Photographic activities"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7483", "Secretarial and translation activities"),
            ("36", "Services to entreprises (except financial)", "D - Services & other", "7484", "Other business activities n.e.c."),
            
                        # ==================== CATÉGORIE 37 ====================
            ("37", "Private and households' services", "D - Services & other", "5270", "Repair of personal and household goods"),
            ("37", "Private and households' services", "D - Services & other", "5271", "Repair of boots, shoes and other articles of leather"),
            ("37", "Private and households' services", "D - Services & other", "5272", "Repair of electrical household goods"),
            ("37", "Private and households' services", "D - Services & other", "5273", "Repair of watches, clocks and jewellery"),
            ("37", "Private and households' services", "D - Services & other", "5274", "Repair n.e.c."),
            ("37", "Private and households' services", "D - Services & other", "5500", "Hotels and restaurants"),
            ("37", "Private and households' services", "D - Services & other", "5510", "Hotels"),
            ("37", "Private and households' services", "D - Services & other", "5511", "Hotels and motels, with restaurant"),
            ("37", "Private and households' services", "D - Services & other", "5512", "Hotels and motels, without restaurant"),
            ("37", "Private and households' services", "D - Services & other", "5520", "Camping sites and other provision of short-stay accommodation"),
            ("37", "Private and households' services", "D - Services & other", "5521", "Youth hostels and mountain refuges"),
            ("37", "Private and households' services", "D - Services & other", "5522", "Camping sites, including caravan sites"),
            ("37", "Private and households' services", "D - Services & other", "5523", "Other provision of lodgings n.e.c."),
            ("37", "Private and households' services", "D - Services & other", "5530", "Restaurants"),
            ("37", "Private and households' services", "D - Services & other", "5540", "Bars"),
            ("37", "Private and households' services", "D - Services & other", "5550", "Canteens and catering"),
            ("37", "Private and households' services", "D - Services & other", "5551", "Canteens"),
            ("37", "Private and households' services", "D - Services & other", "5552", "Catering"),
            ("37", "Private and households' services", "D - Services & other", "7140", "Renting of personal and household goods n.e.c."),
            ("37", "Private and households' services", "D - Services & other", "8041", "Driving school activities"),
            ("37", "Private and households' services", "D - Services & other", "9300", "Other service activities"),
            ("37", "Private and households' services", "D - Services & other", "9301", "Washing and drycleaning of textile and fur products"),
            ("37", "Private and households' services", "D - Services & other", "9302", "Hairdressing and other beauty treatment"),
            ("37", "Private and households' services", "D - Services & other", "9303", "Funeral and related activities"),
            ("37", "Private and households' services", "D - Services & other", "9304", "Physical well-being activities"),
            ("37", "Private and households' services", "D - Services & other", "9305", "Other service activities n.e.c."),
            ("37", "Private and households' services", "D - Services & other", "9500", "Private households with employed persons"),

            # ==================== CATÉGORIE 38 ====================
            ("38", "Miscellaneous", "A - Manufacturers", "3620", "Manufacture of jewellery and related articles"),
            ("38", "Miscellaneous", None, "3621", "Striking of coins and medals"),
            ("38", "Miscellaneous", None, "3622", "Manufacture of jewellery and related articles n.e.c."),
            ("38", "Miscellaneous", None, "3630", "Manufacture of musical instruments"),
            ("38", "Miscellaneous", None, "3640", "Manufacture of sports goods"),
            ("38", "Miscellaneous", None, "3650", "Manufacture of games and toys"),
            ("38", "Miscellaneous", None, "3660", "Miscellaneous manufacturing n.e.c"),
            ("38", "Miscellaneous", None, "3661", "Manufacture of imitation jewellery"),
            ("38", "Miscellaneous", None, "3662", "Manufacture of brooms and brushes"),
            ("38", "Miscellaneous", None, "3663", "Other manufacturing n.e.c."),
            ("38", "Miscellaneous", "D - Services & other", "9271", "Gambling and betting activities"),

            # ==================== CATÉGORIE 39 ====================
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7310", "Research and development in the physical and natural sciences"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7320", "Research and development in the humanities and social sciences"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7400", "Services provided mainly to enterprises"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7410", "Legal, accounting and management advisory activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7411", "Legal activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7412", "Accounting activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7413", "Market research and surveys"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7414", "Business and management consulting"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7415", "Business Administration"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7420", "Architectural and engineering activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7430", "Control activities and technical analyzes"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7440", "Advertising"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7450", "Selection and supply of staff"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7460", "Investigations and security"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7470", "Cleaning activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "748", "Miscellaneous services provided mainly to enterprises"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7480", "Miscellaneous services provided mainly to enterprises"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7481", "Photographic activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7482", "Packaging under pressure"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7483", "Secretariat, translation and routing"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7484", "Other business services n.e.c."),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7500", "Public administration"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7510", "General administration, economic and social"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7511", "General public administration"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7512", "Supervision of social activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7513", "Supervision of economic activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7514", "Support activities for administrations"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7520", "Public prerogative services"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7521", "Foreign Affairs"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7522", "Defense"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7523", "Justice"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7524", "Police"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7525", "Civil protection"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "7530", "Compulsory social security"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8000", "Education"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8010", "Primary education"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8020", "Secondary education"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8021", "General secondary education"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8022", "Technical or vocational secondary education"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8030", "Higher education"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8040", "Continuing training and other educational activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8041", "Driving schools"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8042", "Continuing education in various subjects"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8500", "Health and social work"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8510", "Activities for human health"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8511", "Hospital activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8512", "Medical practice"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8513", "Dental practice"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8514", "Other activities for human health"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8520", "Veterinary activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8530", "Social action"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8531", "Social work with accommodation"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "8532", "Social work without accommodation"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9000", "Sanitation, roads and waste management"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9100", "Associative activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9110", "Economic organizations"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9111", "Employers' and consular organizations"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9112", "Professional organizations"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9120", "Trade unions of employees"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9130", "Other associations"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9131", "Religious organizations"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9132", "Political organizations"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9133", "Associations n.e.c."),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9200", "Recreational, cultural and sports activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9210", "Cinematographic and video activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9211", "Film production"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9212", "Distribution of films"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9213", "Film projection"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9220", "Radio and television activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9230", "Other entertainment activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9231", "Dramatic art and music"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9232", "Management of concert halls"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9233", "Carnival rides and amusement parks"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9234", "Various entertainment activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9250", "Other cultural activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9251", "Library Management"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9252", "Management of cultural heritage"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9253", "Natural heritage management"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9260", "Sport-related activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9261", "Management of sports facilities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9262", "Other sports activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9270", "Recreational activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9271", "Gambling"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9272", "Other recreational activities"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9300", "Personal services"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9301", "Laundry and dyeing"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9302", "Hairdressing and beauty treatments"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9303", "Funeral services"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9304", "Body care"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9305", "Other personal services"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9500", "Domestic services"),
            ("39", "Miscellaneous and Public Administration", "Other Public Services", "9900", "Extra-territorial activities"),
            
            
        ]

        try:
            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be saved"))
                # Simuler sans transaction
                self.simulate_import()
            else:
                with transaction.atomic():
                    # Étape 1: Vider les données existantes si demandé
                    if clear_data:
                        self.clear_existing_data()
                    
                    # Étape 2: Importer les nouvelles données
                    self.import_data(nace_entries, poids_categories)
                    
                    self.stdout.write(self.style.SUCCESS('Successfully imported NACE data!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise
    
    def clear_existing_data(self):
        """Vide toutes les données existantes des catégories et sous-catégories NACE"""
        self.stdout.write(self.style.WARNING('Clearing existing NACE data...'))
        
        # Compter avant suppression
        categories_count = CategoryNaceCode.objects.count()
        subcategories_count = SubCategoryNaceCode.objects.count()
        
        # Supprimer dans l'ordre inverse des dépendances
        # D'abord les sous-catégories (dépendent des catégories)
        SubCategoryNaceCode.objects.all().delete()
        
        # Ensuite les catégories
        CategoryNaceCode.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(
            f'Cleared {categories_count} categories and {subcategories_count} subcategories.'
        ))
    
    def import_data(self, entries, poids_categories):
        category_map = {}
        categories_created = 0
        subcategories_created = 0
        
        self.stdout.write("Starting NACE data import...")
        
        # Traiter chaque entrée
        for i, (activity_code, activity_name, type_code, nace_code, denomination) in enumerate(entries, 1):
            # Gérer la catégorie
            if activity_code not in category_map:
                # Récupérer le poids pour cette catégorie
                poids = poids_categories.get(activity_code, 0.0)
                
                category, created = CategoryNaceCode.objects.update_or_create(
                    code=activity_code,
                    defaults={
                        'libelle': activity_name,
                        'active': True,
                        'poids': poids,
                    }
                )
                category_map[activity_code] = category
                
                if created:
                    categories_created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Created category: {activity_code} - {activity_name} (poids: {poids})'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'↻ Updated category: {activity_code} - {activity_name} (poids: {poids})'
                    ))
            
            category = category_map[activity_code]
            
            # Créer le libellé complet
            full_libelle = denomination
            if type_code:
                full_libelle = f"[{type_code}] {denomination}"
            
            # Pour les sous-catégories, utiliser le même poids que la catégorie
            poids_subcategory = poids_categories.get(activity_code, 0.0)
            
            # Gérer la sous-catégorie
            subcategory, created = SubCategoryNaceCode.objects.update_or_create(
                code=nace_code,
                defaults={
                    'category': category,
                    'libelle': full_libelle,
                    'active': True,
                    'poids': poids_subcategory,
                }
            )
            
            if created:
                subcategories_created += 1
                # Afficher un point tous les 20 enregistrements pour suivre la progression
                if i % 20 == 0:
                    self.stdout.write(f"  Processed {i} entries...")
        
        # Résumé final
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f'Import completed!'))
        self.stdout.write(f"Total categories: {len(category_map)}")
        self.stdout.write(f"Total subcategories created: {subcategories_created}")
        self.stdout.write("="*50)



# Pour les sous-catégories avec poids spécifiques
# Si certaines sous-catégories ont des poids différents de leur catégorie parent, vous pouvez créer un dictionnaire supplémentaire :

# Dictionnaire des poids par sous-catégorie (code NACE spécifique)
# poids_subcategories = {
#     "0100": 0.5,
#     "0110": 0.5,
#     # ... ajoutez tous les codes NACE avec leurs poids spécifiques
# }

# Puis dans import_data(), utilisez :
# poids_subcategory = poids_subcategories.get(nace_code, poids_categories.get(activity_code, 0.0))        
        
        
        
# Import normal
# python manage.py import_nace_codes

# Simulation (dry run)
# python manage.py import_nace_codes --dry-run

# Effacer et réimporter
# python manage.py import_nace_codes --clear

# Version simple
# python manage.py import_nace_simple