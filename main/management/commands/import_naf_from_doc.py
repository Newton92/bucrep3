"""
Importe CategoryNafCode et SubCategoryNafCode — codes NAF feuilles uniquement.

Seuls les vrais codes opérationnels sont importés (regex ^\d{2}\.\d+[A-Z]$).
Les titres de division (ex: "01") et les groupes intermédiaires (ex: "01.1")
sont exclus car ils sont des titres hiérarchiques, pas des codes NAF utilisables.

Usage :
    python manage.py import_naf_from_doc
    python manage.py import_naf_from_doc --dry-run
    python manage.py import_naf_from_doc --clear
"""

import re
from django.core.management.base import BaseCommand
from django.db import transaction

# Regex : seuls les vrais codes NAF feuilles (se terminent par une lettre A-Z)
NAF_LEAF_RE = re.compile(r'^\d{2}\.\d+[A-Z]$')

# ── Catégories NAF (sections A–Q) ─────────────────────────────────────────────
# Format : (code, libelle_fr, libelle_en, poids)
NAF_CATEGORIES = [
    ("A", "Agriculture, chasse, sylviculture",                                "Agriculture, Hunting and Forestry",                            0.5),
    ("B", "Pêche, aquaculture, services annexes",                             "Fishing, Aquaculture and Related Services",                    0.5),
    ("C", "Industries extractives",                                           "Mining and Quarrying",                                         1.0),
    ("D", "Industrie manufacturière",                                         "Manufacturing",                                                1.0),
    ("E", "Production et distribution d'électricité, de gaz et d'eau",       "Electricity, Gas and Water Supply",                            1.0),
    ("F", "Construction",                                                     "Construction",                                                 0.1),
    ("G", "Commerce ; réparations automobile et d'articles domestiques",      "Wholesale and Retail Trade; Repair of Motor Vehicles",         0.2),
    ("H", "Hôtels et restaurants",                                            "Hotels and Restaurants",                                       0.1),
    ("I", "Transports et communications",                                     "Transport, Storage and Communication",                         0.2),
    ("J", "Activités financières",                                            "Financial Intermediation",                                     1.0),
    ("K", "Immobilier, locations et services aux entreprises",                "Real Estate, Renting and Business Activities",                 0.5),
    ("L", "Administration publique",                                          "Public Administration and Defence",                            0.0),
    ("M", "Éducation",                                                        "Education",                                                    0.0),
    ("N", "Santé et action sociale",                                          "Health and Social Work",                                       0.0),
    ("O", "Services collectifs, sociaux et personnels",                       "Other Community, Social and Personal Service Activities",      0.1),
    ("P", "Activités des ménages en tant qu'employeurs",                      "Activities of Private Households as Employers",                0.0),
    ("Q", "Activités extra-territoriales",                                    "Extra-territorial Organizations and Bodies",                   0.0),
]

# ── Codes NAF feuilles uniquement ─────────────────────────────────────────────
# Format : (section, code, libelle_fr, libelle_en)
# Source : document NACE_NAF ENTREPRISE FRANCAIS — codes opérationnels uniquement
NAF_CODES = [
    # ── A — Agriculture, chasse, sylviculture ─────────────────────────────────
    ("A","01.1A","Culture de céréales ; cultures industrielles","Growing of cereals and industrial crops"),
    ("A","01.1C","Culture de légumes ; horticulture ; pépinières","Growing of vegetables and horticultural specialties"),
    ("A","01.1D","Horticulture ; pépinières","Horticulture and nursery activities"),
    ("A","01.1E","Sylviculture","Silviculture"),
    ("A","01.2A","Élevage de bovins","Farming of cattle and buffaloes"),
    ("A","01.2B","Élevage d'équidés","Farming of horses and other equines"),
    ("A","01.2C","Élevage d'ovins et de caprins","Farming of sheep and goats"),
    ("A","01.2D","Élevage de porcins","Farming of swine"),
    ("A","01.2E","Élevage de volailles","Farming of poultry"),
    ("A","01.2F","Élevage d'autres animaux","Farming of other animals"),
    ("A","01.3Z","Culture et élevage associés","Mixed farming"),
    ("A","01.4A","Services aux cultures","Service activities incidental to crop production"),
    ("A","01.4B","Services aux élevages","Service activities incidental to animal production"),
    ("A","01.4C","Aménagement des paysages (parcs, jardins, terrains de sport)","Landscape services (parks, gardens, sports grounds)"),
    ("A","01.5Z","Chasse","Hunting and trapping"),
    ("A","02.0A","Sylviculture et exploitation forestière","Silviculture and forestry"),
    ("A","02.0B","Services annexes à la sylviculture","Service activities incidental to forestry"),

    # ── B — Pêche, aquaculture ────────────────────────────────────────────────
    ("B","05.0A","Pêche","Fishing"),
    ("B","05.0C","Pisciculture, aquaculture","Fish farming and aquaculture"),

    # ── C — Industries extractives ────────────────────────────────────────────
    ("C","10.1Z","Extraction et agglomération de la houille","Mining and agglomeration of hard coal"),
    ("C","10.2Z","Extraction et agglomération du lignite","Mining and agglomeration of lignite"),
    ("C","10.3Z","Extraction et agglomération de la tourbe","Extraction and agglomeration of peat"),
    ("C","11.1Z","Extraction d'hydrocarbures","Extraction of crude petroleum and natural gas"),
    ("C","11.2Z","Services annexes à l'extraction d'hydrocarbures","Service activities incidental to oil and gas extraction"),
    ("C","12.0Z","Extraction de minerais d'uranium","Mining of uranium and thorium ores"),
    ("C","13.1Z","Extraction de minerais de fer","Mining of iron ores"),
    ("C","13.2Z","Extraction de minerais de métaux non ferreux","Mining of non-ferrous metal ores"),
    ("C","14.1Z","Extraction de pierres","Quarrying of stone"),
    ("C","14.2Z","Extraction de sables et d'argiles","Operation of gravel and sand pits; mining of clays"),
    ("C","14.3Z","Extraction de minéraux pour l'industrie chimique","Mining of chemical and fertilizer minerals"),
    ("C","14.4Z","Production de sel","Production of salt"),
    ("C","14.5C","Services annexes aux industries extractives","Service activities incidental to other mining and quarrying"),

    # ── D — Industrie manufacturière ──────────────────────────────────────────
    ("D","15.1A","Production de viandes de boucherie","Production of meat from livestock"),
    ("D","15.1C","Production de viandes de volailles","Production of poultry meat"),
    ("D","15.1D","Charcuterie","Production of meat products"),
    ("D","15.2Z","Industrie du poisson","Processing and preserving of fish"),
    ("D","15.3A","Transformation et conservation de pommes de terre","Processing and preserving of potatoes"),
    ("D","15.3B","Transformation et conservation de légumes","Processing and preserving of vegetables"),
    ("D","15.3C","Transformation et conservation de fruits","Processing and preserving of fruit and nuts"),
    ("D","15.4A","Fabrication d'huiles et graisses brutes","Manufacture of crude oils and fats"),
    ("D","15.4B","Fabrication d'huiles et graisses raffinées","Manufacture of refined oils and fats"),
    ("D","15.4C","Fabrication de margarine","Manufacture of margarine and similar edible fats"),
    ("D","15.5A","Fabrication de lait liquide et de produits frais","Processing of liquid milk and fresh dairy products"),
    ("D","15.5B","Fabrication de beurre","Manufacture of butter"),
    ("D","15.5C","Fabrication de fromages","Manufacture of cheese"),
    ("D","15.5D","Fabrication d'autres produits laitiers","Manufacture of other dairy products"),
    ("D","15.5E","Fabrication de glaces et sorbets","Manufacture of ice cream"),
    ("D","15.6A","Meunerie","Grain mill products"),
    ("D","15.6B","Fabrication de produits amylacés","Manufacture of starches and starch products"),
    ("D","15.7A","Fabrication d'aliments pour animaux de ferme","Manufacture of prepared feeds for farm animals"),
    ("D","15.7B","Fabrication d'aliments pour animaux de compagnie","Manufacture of prepared pet foods"),
    ("D","15.8A","Fabrication industrielle de pain et de pâtisserie fraîche","Industrial manufacture of bread and fresh pastry"),
    ("D","15.8B","Cuisson de produits de boulangerie-pâtisserie","Baking of bread and pastry products"),
    ("D","15.8C","Biscotterie, biscuiterie, pâtisserie de conservation","Manufacture of rusks, biscuits and preserved pastry"),
    ("D","15.8D","Fabrication de sucre","Manufacture of sugar"),
    ("D","15.8E","Chocolaterie, confiserie","Manufacture of cocoa, chocolate and sugar confectionery"),
    ("D","15.8F","Fabrication de pâtes alimentaires","Manufacture of macaroni, noodles and similar farinaceous products"),
    ("D","15.8G","Transformation du thé et du café","Processing of tea and coffee"),
    ("D","15.8H","Fabrication de condiments et assaisonnements","Manufacture of condiments and seasonings"),
    ("D","15.8J","Fabrication d'aliments homogénéisés et diététiques","Manufacture of homogenised food preparations and dietetic food"),
    ("D","15.8K","Fabrication d'autres produits alimentaires","Manufacture of other food products"),
    ("D","15.9A","Production de boissons alcooliques distillées","Manufacture of distilled potable alcoholic beverages"),
    ("D","15.9B","Fabrication de vins","Manufacture of wines"),
    ("D","15.9D","Fabrication de bière","Manufacture of beer"),
    ("D","15.9E","Fabrication de malt","Manufacture of malt"),
    ("D","15.9F","Industrie des eaux de table, limonades","Manufacture of soft drinks; production of mineral waters"),
    ("D","16.0Z","Fabrication de produits à base de tabac","Manufacture of tobacco products"),
    ("D","17.1A","Filature de l'industrie cotonnière","Preparation and spinning of cotton-type fibres"),
    ("D","17.1B","Filature de l'industrie lainière — cycle cardé","Preparation and spinning of woollen-type fibres"),
    ("D","17.1C","Filature de l'industrie lainière — cycle peigné","Preparation and spinning of worsted-type fibres"),
    ("D","17.1D","Préparation et filature de lin","Preparation and spinning of flax-type fibres"),
    ("D","17.1F","Moulinage et texturation de la soie","Throwing and preparation of silk"),
    ("D","17.1G","Fabrication de fils à coudre","Manufacture of sewing threads"),
    ("D","17.1H","Préparation et filature d'autres fibres","Preparation and spinning of other textile fibres"),
    ("D","17.2A","Tissage de l'industrie cotonnière","Cotton-type weaving"),
    ("D","17.2B","Tissage de l'industrie lainière","Woollen-type weaving"),
    ("D","17.2C","Tissage de soieries","Silk-type weaving"),
    ("D","17.2D","Tissage d'autres textiles","Other textile weaving"),
    ("D","17.3Z","Ennoblissement textile","Finishing of textiles"),
    ("D","17.4A","Fabrication d'articles de bonneterie","Manufacture of knitted and crocheted fabrics"),
    ("D","17.4B","Fabrication d'articles chaussants à mailles","Manufacture of knitted and crocheted hosiery"),
    ("D","17.4C","Fabrication de pull-overs et articles similaires","Manufacture of knitted and crocheted pullovers"),
    ("D","17.5A","Fabrication de tapis et moquettes","Manufacture of carpets and rugs"),
    ("D","17.5B","Fabrication de ficelles, cordes et filets","Manufacture of cordage, rope, twine and netting"),
    ("D","17.5C","Fabrication de non-tissés","Manufacture of non-wovens"),
    ("D","17.5E","Fabrication d'autres textiles","Manufacture of other textiles"),
    ("D","17.6Z","Fabrication d'étoffes à mailles","Manufacture of knitted and crocheted fabrics"),
    ("D","17.7Z","Fabrication d'articles textiles","Manufacture of other textiles"),
    ("D","18.1Z","Fabrication de vêtements en cuir","Manufacture of leather clothes"),
    ("D","18.2A","Fabrication de vêtements de travail","Manufacture of workwear"),
    ("D","18.2B","Fabrication de vêtements de dessus pour hommes","Manufacture of other men's outerwear"),
    ("D","18.2C","Fabrication de vêtements de dessus pour femmes","Manufacture of other women's outerwear"),
    ("D","18.2D","Fabrication de vêtements de dessous","Manufacture of underwear"),
    ("D","18.2E","Fabrication d'autres vêtements et accessoires","Manufacture of other wearing apparel and accessories"),
    ("D","18.3Z","Apprêt et teinture de fourrures","Dressing and dyeing of fur"),
    ("D","19.1Z","Apprêt et tannage des cuirs","Tanning and dressing of leather"),
    ("D","19.2Z","Fabrication d'articles de voyage, de maroquinerie","Manufacture of luggage, handbags and the like"),
    ("D","19.3Z","Fabrication de chaussures","Manufacture of footwear"),
    ("D","20.1Z","Sciage et rabotage du bois","Sawmilling and planing of wood"),
    ("D","20.2Z","Fabrication de panneaux de bois","Manufacture of veneer sheets; manufacture of plywood"),
    ("D","20.3Z","Fabrication de charpentes et de menuiseries","Manufacture of builders' carpentry and joinery"),
    ("D","20.4Z","Fabrication d'emballages en bois","Manufacture of wooden containers"),
    ("D","20.5A","Fabrication d'objets divers en bois","Manufacture of other products of wood"),
    ("D","20.5B","Fabrication de liège, vannerie, sparterie","Manufacture of articles of cork, straw and plaiting materials"),
    ("D","21.1A","Fabrication de pâte à papier","Manufacture of pulp"),
    ("D","21.1B","Fabrication de papier et de carton","Manufacture of paper and paperboard"),
    ("D","21.2A","Fabrication de carton ondulé et d'emballages","Manufacture of corrugated paper and paperboard"),
    ("D","21.2B","Fabrication de cartonnages","Manufacture of other containers of paper and paperboard"),
    ("D","21.2C","Fabrication d'emballages en papier","Manufacture of paper and paperboard packing containers"),
    ("D","21.2D","Fabrication d'articles en papier à usage sanitaire","Manufacture of household and sanitary goods of paper"),
    ("D","21.2E","Fabrication de papiers peints","Manufacture of wallpaper"),
    ("D","21.2F","Fabrication d'autres articles en papier ou en carton","Manufacture of other articles of paper and paperboard"),
    ("D","22.1A","Édition de livres","Publishing of books"),
    ("D","22.1B","Édition de journaux","Publishing of newspapers"),
    ("D","22.1C","Édition de revues et périodiques","Publishing of journals and periodicals"),
    ("D","22.1E","Édition d'enregistrements sonores","Publishing of recorded media"),
    ("D","22.1F","Autres éditions","Other publishing"),
    ("D","22.2A","Imprimerie de journaux","Printing of newspapers"),
    ("D","22.2B","Autre imprimerie","Other printing"),
    ("D","22.2C","Reliure et finition","Bookbinding and finishing"),
    ("D","22.2D","Composition et photogravure","Composition and plate-making"),
    ("D","22.2E","Autres activités graphiques","Other pre-press activities"),
    ("D","22.3A","Reproduction de supports informatiques","Reproduction of computer media"),
    ("D","22.3B","Reproduction d'enregistrements sonores","Reproduction of sound recording"),
    ("D","22.3C","Reproduction d'enregistrements vidéo","Reproduction of video recording"),
    ("D","23.1Z","Cokéfaction","Manufacture of coke oven products"),
    ("D","23.2Z","Raffinage de pétrole","Manufacture of refined petroleum products"),
    ("D","23.3Z","Elaboration et transformation de matières nucléaires","Processing of nuclear fuel"),
    ("D","24.1A","Fabrication de gaz industriels","Manufacture of industrial gases"),
    ("D","24.1B","Fabrication de colorants et de pigments","Manufacture of dyes and pigments"),
    ("D","24.1C","Fabrication d'autres produits chimiques inorganiques","Manufacture of other inorganic basic chemicals"),
    ("D","24.1D","Fabrication d'autres produits chimiques organiques","Manufacture of other organic basic chemicals"),
    ("D","24.1E","Fabrication de produits azotés et d'engrais","Manufacture of fertilisers and nitrogen compounds"),
    ("D","24.1F","Fabrication de matières plastiques","Manufacture of plastics in primary forms"),
    ("D","24.1G","Fabrication de caoutchouc synthétique","Manufacture of synthetic rubber in primary forms"),
    ("D","24.2Z","Fabrication de produits agrochimiques","Manufacture of pesticides and other agrochemical products"),
    ("D","24.3Z","Fabrication de peintures et vernis","Manufacture of paints, varnishes and similar coatings"),
    ("D","24.4A","Fabrication de produits pharmaceutiques de base","Manufacture of basic pharmaceutical products"),
    ("D","24.4B","Fabrication de médicaments","Manufacture of pharmaceutical preparations"),
    ("D","24.4C","Fabrication d'autres produits pharmaceutiques","Manufacture of other pharmaceutical products"),
    ("D","24.5A","Fabrication de savons, détergents et produits d'entretien","Manufacture of soap and detergents"),
    ("D","24.5B","Fabrication de parfums et de produits pour la toilette","Manufacture of perfumes and toilet preparations"),
    ("D","24.6A","Fabrication d'huiles essentielles","Manufacture of essential oils"),
    ("D","24.6B","Fabrication de produits explosifs","Manufacture of explosives"),
    ("D","24.6C","Fabrication de colles et gélatines","Manufacture of glues and gelatines"),
    ("D","24.6D","Fabrication d'huiles essentielles et arômes","Manufacture of essential oils and aromatic products"),
    ("D","24.6E","Fabrication de produits chimiques à usage photographique","Manufacture of photographic chemical material"),
    ("D","24.6F","Fabrication de supports de données magnétiques","Manufacture of prepared unrecorded media"),
    ("D","24.6G","Fabrication de produits chimiques divers","Manufacture of other chemical products"),
    ("D","24.7Z","Fabrication de fibres artificielles ou synthétiques","Manufacture of man-made fibres"),
    ("D","25.1A","Fabrication de pneumatiques","Manufacture of rubber tyres and tubes"),
    ("D","25.1B","Rechapage de pneumatiques","Retreading and rebuilding of rubber tyres"),
    ("D","25.1C","Fabrication d'autres articles en caoutchouc","Manufacture of other rubber products"),
    ("D","25.2A","Fabrication de plaques, feuilles, tubes et profilés","Manufacture of plastic plates, sheets, tubes and profiles"),
    ("D","25.2B","Fabrication d'emballages en matières plastiques","Manufacture of plastic packing goods"),
    ("D","25.2C","Fabrication d'éléments en matières plastiques pour la construction","Manufacture of builder's ware of plastic"),
    ("D","25.2D","Fabrication d'articles divers en matières plastiques","Manufacture of other plastic products"),
    ("D","26.1A","Fabrication de verre plat","Manufacture of flat glass"),
    ("D","26.1B","Façonnage et transformation du verre plat","Manufacture of shaped and processed flat glass"),
    ("D","26.1C","Fabrication de verre creux","Manufacture of hollow glass"),
    ("D","26.1D","Fabrication de fibres de verre","Manufacture of glass fibres"),
    ("D","26.1E","Fabrication et façonnage d'autres articles en verre","Manufacture of other glass articles"),
    ("D","26.2A","Fabrication de produits céramiques","Manufacture of ceramic household and ornamental articles"),
    ("D","26.2B","Fabrication d'appareils sanitaires en céramique","Manufacture of ceramic sanitary fixtures"),
    ("D","26.2C","Fabrication d'isolateurs en céramique","Manufacture of ceramic insulators and insulating fittings"),
    ("D","26.2D","Fabrication d'autres produits céramiques","Manufacture of other ceramic products"),
    ("D","26.2E","Fabrication de carreaux en céramique","Manufacture of ceramic floor and wall tiles"),
    ("D","26.3Z","Fabrication de tuiles et briques","Manufacture of ceramic tiles and flags"),
    ("D","26.4Z","Fabrication de ciment, chaux et plâtre","Manufacture of cement, lime and plaster"),
    ("D","26.5A","Fabrication d'ouvrages en béton","Manufacture of concrete products for construction purposes"),
    ("D","26.5B","Fabrication de plâtre et d'articles en plâtre","Manufacture of plaster products for construction purposes"),
    ("D","26.6Z","Fabrication d'éléments en béton, en ciment ou en plâtre","Manufacture of concrete, plaster and cement products"),
    ("D","26.7Z","Taille, façonnage et finissage de la pierre","Cutting, shaping and finishing of ornamental and building stone"),
    ("D","26.8A","Fabrication de produits abrasifs","Manufacture of abrasive products"),
    ("D","26.8B","Fabrication de produits minéraux non métalliques","Manufacture of other non-metallic mineral products"),
    ("D","27.1Z","Sidérurgie","Manufacture of basic iron and steel"),
    ("D","27.2A","Fabrication de tubes en fonte","Manufacture of cast iron tubes"),
    ("D","27.2B","Fabrication de tubes en acier","Manufacture of steel tubes"),
    ("D","27.3A","Étirage à froid","Cold drawing of bars"),
    ("D","27.3B","Laminage à froid de feuillards","Cold rolling of narrow strip"),
    ("D","27.3C","Profilage à froid par formage ou pliage","Cold forming or folding"),
    ("D","27.3D","Tréfilage à froid","Cold drawing of wire"),
    ("D","27.4A","Production de métaux précieux","Precious metals production"),
    ("D","27.4B","Production d'aluminium","Production of aluminium"),
    ("D","27.4C","Production de plomb, zinc ou étain","Production of lead, zinc and tin"),
    ("D","27.4D","Production de cuivre","Production of copper"),
    ("D","27.4E","Production d'autres métaux non ferreux","Production of other non-ferrous metals"),
    ("D","27.5A","Fonderie de fonte","Casting of iron"),
    ("D","27.5B","Fonderie d'acier","Casting of steel"),
    ("D","27.5C","Fonderie de métaux légers","Casting of light metals"),
    ("D","27.5D","Fonderie d'autres métaux non ferreux","Casting of other non-ferrous metals"),
    ("D","28.1A","Fabrication de structures métalliques","Manufacture of metal structures"),
    ("D","28.1B","Fabrication de portes et fenêtres en métal","Manufacture of metal doors and windows"),
    ("D","28.2A","Fabrication de réservoirs et citernes","Manufacture of tanks, reservoirs and containers of metal"),
    ("D","28.2B","Fabrication de radiateurs et chaudières","Manufacture of central heating radiators and boilers"),
    ("D","28.3Z","Fabrication de générateurs de vapeur","Manufacture of steam generators"),
    ("D","28.4A","Forge, estampage, matriçage, emboutissage","Forging, pressing, stamping and roll forming of metal"),
    ("D","28.4B","Découpage, emboutissage","Powder metallurgy"),
    ("D","28.5A","Traitement et revêtement des métaux","Treatment and coating of metals"),
    ("D","28.5B","Décolletage","Engineering services"),
    ("D","28.5C","Mécanique générale","General mechanical engineering"),
    ("D","28.6A","Fabrication de coutellerie","Manufacture of cutlery"),
    ("D","28.6B","Fabrication d'outillage à main","Manufacture of tools"),
    ("D","28.6C","Fabrication de serrures et ferrures","Manufacture of locks and hinges"),
    ("D","28.7A","Fabrication de fûts et emballages métalliques similaires","Manufacture of steel drums and similar containers"),
    ("D","28.7B","Fabrication d'emballages métalliques légers","Manufacture of light metal packaging"),
    ("D","28.7C","Fabrication d'articles en fils métalliques","Manufacture of wire products"),
    ("D","28.7D","Boulonnerie, visserie","Manufacture of fasteners and screw machine products"),
    ("D","28.7E","Fabrication d'autres produits métalliques","Manufacture of other fabricated metal products"),
    ("D","29.1A","Fabrication d'équipements mécaniques","Manufacture of mechanical power transmission equipment"),
    ("D","29.1B","Fabrication d'organes mécaniques de transmission","Manufacture of other general purpose machinery"),
    ("D","29.1C","Fabrication de fours et brûleurs","Manufacture of furnaces and furnace burners"),
    ("D","29.1D","Fabrication d'équipements de levage et de manutention","Manufacture of lifting and handling equipment"),
    ("D","29.1E","Fabrication d'équipements de bureau","Manufacture of office machinery"),
    ("D","29.1F","Fabrication d'équipements de refroidissement","Manufacture of machinery for food, beverage and tobacco processing"),
    ("D","29.1G","Fabrication d'appareils pour les industries chimiques","Manufacture of machinery for textile, apparel and leather production"),
    ("D","29.2A","Fabrication de machines agricoles","Manufacture of agricultural and forestry machinery"),
    ("D","29.2B","Fabrication de machines de formage des métaux","Manufacture of machine tools for working metal"),
    ("D","29.2C","Fabrication de machines pour la métallurgie","Manufacture of other machine tools"),
    ("D","29.2D","Fabrication de machines pour les mines","Manufacture of machinery for mining, quarrying and construction"),
    ("D","29.2E","Fabrication de machines pour l'industrie agro-alimentaire","Manufacture of machinery for food, beverage and tobacco processing"),
    ("D","29.2F","Fabrication de machines pour le textile","Manufacture of machinery for textile production"),
    ("D","29.2G","Fabrication de machines pour le papier","Manufacture of machinery for paper and paperboard production"),
    ("D","29.3A","Fabrication d'équipements automobiles","Manufacture of motor vehicles"),
    ("D","29.3B","Fabrication de carrosseries automobiles","Manufacture of bodies for motor vehicles"),
    ("D","29.4A","Fabrication d'outils portatifs à moteur incorporé","Manufacture of power-driven hand tools"),
    ("D","29.4B","Fabrication d'équipements frigorifiques industriels","Manufacture of refrigerating and ventilating equipment"),
    ("D","29.4C","Fabrication d'autres machines d'usage général","Manufacture of other general purpose machinery"),
    ("D","29.5A","Fabrication de machines pour la métallurgie","Manufacture of machinery for metallurgy"),
    ("D","29.5B","Fabrication de machines pour l'extraction","Manufacture of machinery for mining, quarrying and construction"),
    ("D","29.5C","Fabrication de machines pour l'industrie alimentaire","Manufacture of machinery for food, beverage and tobacco processing"),
    ("D","29.5D","Fabrication de machines pour les industries textiles","Manufacture of machinery for textile, apparel and leather production"),
    ("D","29.5E","Fabrication de machines pour le papier et le carton","Manufacture of machinery for paper and paperboard production"),
    ("D","29.5F","Fabrication d'autres machines spécialisées","Manufacture of other special purpose machinery"),
    ("D","29.6Z","Fabrication d'armes et de munitions","Manufacture of weapons and ammunition"),
    ("D","29.7A","Fabrication d'appareils électroménagers","Manufacture of electric domestic appliances"),
    ("D","29.7B","Fabrication d'appareils ménagers non électriques","Manufacture of non-electric domestic appliances"),
    ("D","30.0Z","Fabrication de machines de bureau et de matériel informatique","Manufacture of office machinery and computers"),
    ("D","31.1Z","Fabrication de moteurs, génératrices et transformateurs","Manufacture of electric motors, generators and transformers"),
    ("D","31.2Z","Fabrication de matériel de distribution et de commande électrique","Manufacture of electricity distribution and control apparatus"),
    ("D","31.3Z","Fabrication de fils et câbles isolés","Manufacture of insulated wire and cable"),
    ("D","31.4Z","Fabrication d'accumulateurs et de piles électriques","Manufacture of accumulators, primary cells and primary batteries"),
    ("D","31.5A","Fabrication de lampes","Manufacture of electric lamps and lighting equipment"),
    ("D","31.5B","Fabrication d'appareils d'éclairage","Manufacture of other lighting equipment"),
    ("D","31.6A","Fabrication de matériels électriques","Manufacture of electrical equipment for engines and vehicles"),
    ("D","31.6B","Fabrication d'autres matériels électriques","Manufacture of other electrical equipment"),
    ("D","32.1Z","Fabrication de composants électroniques passifs","Manufacture of electronic components"),
    ("D","32.2Z","Fabrication d'émetteurs de radiodiffusion","Manufacture of television and radio transmitters"),
    ("D","32.3Z","Fabrication d'appareils de réception","Manufacture of television and radio receivers"),
    ("D","33.1A","Fabrication de matériel médico-chirurgical","Manufacture of medical and surgical equipment"),
    ("D","33.1B","Fabrication de matériel médical","Manufacture of medical apparatus and instruments"),
    ("D","33.2Z","Fabrication d'instruments de mesure et de contrôle","Manufacture of instruments for measuring, checking and testing"),
    ("D","33.3Z","Fabrication d'équipements de contrôle des processus industriels","Manufacture of industrial process control equipment"),
    ("D","33.4Z","Fabrication d'instruments d'optique et de matériel photographique","Manufacture of optical instruments and photographic equipment"),
    ("D","33.5Z","Fabrication de montres et horloges","Manufacture of watches and clocks"),
    ("D","34.1Z","Construction de véhicules automobiles","Manufacture of motor vehicles"),
    ("D","34.2Z","Fabrication de carrosseries, remorques et semi-remorques","Manufacture of bodies for motor vehicles"),
    ("D","34.3Z","Fabrication d'équipements automobiles","Manufacture of parts and accessories for motor vehicles"),
    ("D","35.1A","Construction de bateaux de plaisance","Building and repairing of pleasure and sporting boats"),
    ("D","35.1B","Construction de navires civils","Building and repairing of ships"),
    ("D","35.2Z","Fabrication de matériel ferroviaire roulant","Manufacture of railway and tramway locomotives and rolling stock"),
    ("D","35.3Z","Construction aéronautique et spatiale","Manufacture of aircraft and spacecraft"),
    ("D","35.4Z","Fabrication de motocycles","Manufacture of motorcycles"),
    ("D","35.5Z","Fabrication d'autres matériels de transport","Manufacture of other transport equipment"),
    ("D","36.1A","Fabrication de sièges","Manufacture of chairs and seats"),
    ("D","36.1B","Fabrication de meubles de bureau et de magasin","Manufacture of office and shop furniture"),
    ("D","36.1C","Fabrication de meubles de cuisine","Manufacture of kitchen furniture"),
    ("D","36.1D","Fabrication de meubles de salle de bains","Manufacture of other furniture"),
    ("D","36.1E","Fabrication de meubles divers","Manufacture of other furniture"),
    ("D","36.1F","Fabrication de matelas","Manufacture of mattresses"),
    ("D","36.2A","Fabrication de monnaies","Striking of coins"),
    ("D","36.2B","Bijouterie, joaillerie","Manufacture of jewellery and related articles"),
    ("D","36.3Z","Fabrication d'instruments de musique","Manufacture of musical instruments"),
    ("D","36.4Z","Fabrication d'articles de sport","Manufacture of sports goods"),
    ("D","36.5Z","Fabrication de jeux et jouets","Manufacture of games and toys"),
    ("D","36.6A","Fabrication de bijoux fantaisie","Manufacture of imitation jewellery"),
    ("D","36.6B","Fabrication d'articles de bureau","Manufacture of office supplies"),
    ("D","36.6C","Fabrication d'articles de brosserie","Manufacture of brooms and brushes"),
    ("D","36.6D","Autres fabrications diverses","Other manufacturing"),
    ("D","37.1Z","Récupération de matières métalliques recyclables","Recycling of metal waste and scrap"),
    ("D","37.2Z","Récupération de matières non métalliques recyclables","Recycling of non-metal waste and scrap"),

    # ── E — Électricité, gaz et eau ───────────────────────────────────────────
    ("E","40.1A","Production d'électricité","Production of electricity"),
    ("E","40.1B","Transport d'électricité","Transmission of electricity"),
    ("E","40.1C","Distribution et commerce d'électricité","Distribution of electricity"),
    ("E","40.2A","Production et distribution de gaz naturel","Manufacture of gas"),
    ("E","40.2B","Distribution et commerce de combustibles gazeux","Distribution and trade of gaseous fuels"),
    ("E","40.3Z","Production et distribution de vapeur et d'eau chaude","Steam and hot water supply"),
    ("E","41.0Z","Captage, traitement et distribution d'eau","Collection, purification and distribution of water"),
    ("E","41.0A","Captage et traitement des eaux","Water collection and purification"),
    ("E","41.0B","Distribution d'eau","Water distribution"),

    # ── F — Construction ──────────────────────────────────────────────────────
    ("F","45.1A","Terrassements courants et travaux préparatoires","Demolition and site preparation"),
    ("F","45.1B","Terrassements de grande masse","Earthmoving"),
    ("F","45.2A","Construction de maisons individuelles","Construction of residential buildings"),
    ("F","45.2B","Construction de bâtiments divers","Construction of other buildings"),
    ("F","45.2C","Construction de routes et autoroutes","Construction of motorways, roads, airfields and sport facilities"),
    ("F","45.2D","Construction de voies ferrées","Construction of railways and underground railways"),
    ("F","45.2E","Construction d'ouvrages d'art","Construction of bridges, elevated highways, tunnels and subways"),
    ("F","45.2F","Construction de réseaux divers","Construction of pipelines, communication and power lines"),
    ("F","45.2G","Construction d'autres ouvrages de génie civil","Other construction of civil engineering projects"),
    ("F","45.2H","Construction de lignes électriques et de télécommunications","Construction of electricity distribution and telecommunications lines"),
    ("F","45.2J","Forage et sondage","Other specialised construction activities"),
    ("F","45.3A","Travaux d'installation électrique","Electrical installation"),
    ("F","45.3B","Travaux d'isolation","Insulation work activities"),
    ("F","45.3C","Installation de climatisation et de ventilation","Installation of heating and ventilation equipment"),
    ("F","45.3D","Autres travaux d'installation","Other building installation"),
    ("F","45.4A","Plâtrerie","Plastering"),
    ("F","45.4B","Menuiserie bois et matières plastiques","Joinery installation"),
    ("F","45.4C","Menuiserie métallique, serrurerie","Joinery installation (metal)"),
    ("F","45.4D","Revêtement des sols et des murs","Floor and wall covering"),
    ("F","45.4E","Peinture et vitrerie","Painting and glazing"),
    ("F","45.4F","Agencement de lieux de vente","Shop fitting"),
    ("F","45.4G","Autres travaux de finition","Other building completion"),
    ("F","45.5Z","Location avec opérateur de matériel de construction","Renting of construction or demolition equipment with operator"),

    # ── G — Commerce ──────────────────────────────────────────────────────────
    ("G","50.1Z","Commerce de véhicules automobiles","Sale of motor vehicles"),
    ("G","50.2Z","Entretien et réparation de véhicules automobiles","Maintenance and repair of motor vehicles"),
    ("G","50.3A","Commerce de gros d'équipements automobiles","Wholesale of motor vehicle parts and accessories"),
    ("G","50.3B","Commerce de détail d'équipements automobiles","Retail sale of motor vehicle parts and accessories"),
    ("G","50.4Z","Commerce et réparation de motocycles","Sale, maintenance and repair of motorcycles"),
    ("G","50.5Z","Commerce de détail de carburants","Retail sale of automotive fuel"),
    ("G","51.1A","Intermédiaires du commerce en matières premières agricoles","Agents involved in the sale of agricultural raw materials"),
    ("G","51.1B","Intermédiaires du commerce en combustibles","Agents involved in the sale of fuels"),
    ("G","51.1C","Intermédiaires du commerce en bois et matériaux","Agents involved in the sale of timber and building materials"),
    ("G","51.1D","Intermédiaires du commerce en machines","Agents involved in the sale of machinery"),
    ("G","51.1E","Intermédiaires du commerce en meubles","Agents involved in the sale of furniture, household goods"),
    ("G","51.1F","Intermédiaires du commerce en textiles","Agents involved in the sale of textiles, clothing, footwear"),
    ("G","51.1G","Intermédiaires du commerce en produits alimentaires","Agents involved in the sale of food, beverages and tobacco"),
    ("G","51.1H","Intermédiaires du commerce en produits non alimentaires","Agents involved in the sale of other products"),
    ("G","51.2A","Commerce de gros de céréales et aliments","Wholesale of grain, seeds and animal feeds"),
    ("G","51.2B","Commerce de gros de fleurs et plantes","Wholesale of flowers and plants"),
    ("G","51.2C","Commerce de gros d'animaux vivants","Wholesale of live animals"),
    ("G","51.2D","Commerce de gros de cuirs et peaux","Wholesale of hides, skins and leather"),
    ("G","51.2E","Commerce de gros de tabac non manufacturé","Wholesale of unmanufactured tobacco"),
    ("G","51.3A","Commerce de gros de fruits et légumes","Wholesale of fruit and vegetables"),
    ("G","51.3B","Commerce de gros de viandes et produits à base de viande","Wholesale of meat and meat products"),
    ("G","51.3C","Commerce de gros de produits laitiers","Wholesale of dairy products, eggs and edible oils"),
    ("G","51.3D","Commerce de gros de boissons","Wholesale of beverages"),
    ("G","51.3E","Commerce de gros de tabac","Wholesale of tobacco products"),
    ("G","51.3F","Commerce de gros de sucre, chocolat","Wholesale of sugar and chocolate"),
    ("G","51.3G","Commerce de gros de café, thé, cacao","Wholesale of coffee, tea, cocoa and spices"),
    ("G","51.3H","Commerce de gros d'autres produits alimentaires","Wholesale of other food"),
    ("G","51.4A","Commerce de gros de textiles","Wholesale of textiles"),
    ("G","51.4B","Commerce de gros d'habillement","Wholesale of clothing and footwear"),
    ("G","51.4C","Commerce de gros d'appareils électroménagers","Wholesale of electrical household appliances"),
    ("G","51.4D","Commerce de gros de vaisselle et coutellerie","Wholesale of china and glassware, wallpaper and cleaning materials"),
    ("G","51.4E","Commerce de gros de parfumerie et de produits de beauté","Wholesale of perfume and cosmetics"),
    ("G","51.4F","Commerce de gros de produits pharmaceutiques","Wholesale of pharmaceutical goods"),
    ("G","51.4G","Commerce de gros de meubles","Wholesale of furniture, carpets and lighting equipment"),
    ("G","51.4H","Commerce de gros d'autres biens de consommation","Wholesale of other household goods"),
    ("G","51.5A","Commerce de gros de combustibles","Wholesale of solid, liquid and gaseous fuels"),
    ("G","51.5B","Commerce de gros de métaux et minerais","Wholesale of metals and metal ores"),
    ("G","51.5C","Commerce de gros de bois et de matériaux de construction","Wholesale of wood, construction materials and sanitary equipment"),
    ("G","51.5D","Commerce de gros de quincaillerie","Wholesale of hardware, plumbing and heating equipment"),
    ("G","51.5E","Commerce de gros de fournitures pour l'industrie chimique","Wholesale of chemical products"),
    ("G","51.5F","Commerce de gros d'autres produits intermédiaires","Wholesale of other intermediate products"),
    ("G","51.5G","Commerce de gros de déchets et débris","Wholesale of waste and scrap"),
    ("G","51.6A","Commerce de gros de machines-outils","Wholesale of machine tools"),
    ("G","51.6B","Commerce de gros de machines pour l'industrie","Wholesale of mining, construction and civil engineering machinery"),
    ("G","51.6C","Commerce de gros de machines pour le textile","Wholesale of machinery for the textile industry"),
    ("G","51.6D","Commerce de gros d'ordinateurs","Wholesale of computers, computer peripheral equipment and software"),
    ("G","51.6E","Commerce de gros de composants électroniques","Wholesale of electronic components and telecommunications equipment"),
    ("G","51.6F","Commerce de gros d'autres machines","Wholesale of other machinery"),
    ("G","51.7Z","Autres commerces de gros","Other wholesale"),
    ("G","52.1A","Commerce de détail de produits surgelés","Retail sale of frozen goods"),
    ("G","52.1B","Commerce d'alimentation générale","Non-specialised stores with food, beverages or tobacco predominating"),
    ("G","52.1C","Supérettes","Small supermarkets"),
    ("G","52.1D","Supermarchés","Supermarkets"),
    ("G","52.1E","Magasins populaires","Variety stores"),
    ("G","52.1F","Hypermarchés","Hypermarkets"),
    ("G","52.1G","Autres commerces de détail alimentaires","Other retail sale in non-specialised stores"),
    ("G","52.2A","Commerce de détail de fruits et légumes","Retail sale of fruit and vegetables"),
    ("G","52.2B","Commerce de détail de viandes et produits à base de viande","Retail sale of meat and meat products"),
    ("G","52.2C","Commerce de détail de poissons","Retail sale of fish, crustaceans and molluscs"),
    ("G","52.2D","Commerce de détail de pain, pâtisserie et confiserie","Retail sale of bread, cakes, flour confectionery"),
    ("G","52.2E","Commerce de détail de boissons","Retail sale of beverages"),
    ("G","52.2F","Commerce de détail de tabac","Retail sale of tobacco products"),
    ("G","52.2G","Autres commerces de détail alimentaires spécialisés","Other retail sale of food, beverages and tobacco in specialised stores"),
    ("G","52.3A","Commerce de détail de produits pharmaceutiques","Retail sale of pharmaceutical goods"),
    ("G","52.3B","Commerce de détail d'articles médicaux","Retail sale of medical and orthopaedic goods"),
    ("G","52.3C","Commerce de détail de parfumerie et de produits de beauté","Retail sale of cosmetic and toilet articles"),
    ("G","52.4A","Commerce de détail de textiles","Retail sale of clothing"),
    ("G","52.4B","Commerce de détail d'habillement","Retail sale of clothing"),
    ("G","52.4C","Commerce de détail de la chaussure","Retail sale of footwear and leather goods"),
    ("G","52.4D","Commerce de détail de maroquinerie","Retail sale of leather goods and travel accessories"),
    ("G","52.4E","Commerce de détail de meubles","Retail sale of furniture, lighting equipment and household articles"),
    ("G","52.4F","Commerce de détail d'équipements du foyer","Retail sale of household appliances"),
    ("G","52.4G","Commerce de détail de quincaillerie","Retail sale of hardware, paints and glass"),
    ("G","52.4H","Commerce de détail de livres et journaux","Retail sale of books, newspapers and stationery"),
    ("G","52.4J","Commerce de détail de matériels de sport","Retail sale of sporting equipment"),
    ("G","52.4K","Commerce de détail de jeux et jouets","Retail sale of games and toys"),
    ("G","52.4L","Commerce de détail d'appareils photo","Retail sale of photographic and optical goods, watches and clocks"),
    ("G","52.4M","Commerce de détail d'ordinateurs","Retail sale of computers and office equipment"),
    ("G","52.4N","Commerce de détail de fleurs","Retail sale of flowers, plants, seeds"),
    ("G","52.4P","Commerce de détail d'animaux de compagnie","Retail sale of pet animals and pet food"),
    ("G","52.4Q","Commerce de détail de seconde main","Retail sale of second-hand goods"),
    ("G","52.4R","Autres commerces de détail spécialisés","Other retail sale of new goods in specialised stores"),
    ("G","52.5Z","Commerce de détail de biens d'occasion","Retail sale of second-hand goods"),
    ("G","52.6A","Vente par correspondance","Retail sale via mail order houses"),
    ("G","52.6B","Commerce de détail par éventaires et marchés","Retail sale via stalls and markets"),
    ("G","52.6C","Autres commerces de détail hors magasin","Other retail sale not in stores"),

    # ── H — Hôtels et restaurants ─────────────────────────────────────────────
    ("H","55.1A","Hôtels avec restaurant","Hotels with restaurant"),
    ("H","55.1B","Hôtels de tourisme sans restaurant","Hotels without restaurant"),
    ("H","55.1C","Autres hôtels","Other hotels"),
    ("H","55.2A","Auberges de jeunesse et refuges","Youth hostels and mountain refuges"),
    ("H","55.2B","Hébergement de courte durée","Camping sites and caravan sites"),
    ("H","55.2C","Exploitation de terrains de camping","Operation of camping sites"),
    ("H","55.2D","Hébergement touristique autre","Other provision of lodgings"),
    ("H","55.3A","Restauration de type traditionnel","Restaurants"),
    ("H","55.3B","Restauration de type rapide","Fast food restaurants and take-away food shops"),
    ("H","55.4A","Débits de boissons","Bars"),
    ("H","55.4B","Discothèques et dancings","Night clubs and dance halls"),
    ("H","55.5A","Cantines et restaurants d'entreprises","Canteens"),
    ("H","55.5B","Restauration collective sous contrat","Contract caterers"),
    ("H","55.5C","Traiteurs, organisation de réceptions","Other food service activities"),

    # ── I — Transports et communications ──────────────────────────────────────
    ("I","60.1Z","Transport ferroviaire","Railway transportation"),
    ("I","60.2A","Transports routiers réguliers de voyageurs","Scheduled passenger land transport"),
    ("I","60.2B","Transports urbains de voyageurs","Urban and suburban passenger land transport"),
    ("I","60.2C","Taxis","Taxi operation"),
    ("I","60.2D","Autres transports routiers de voyageurs","Other passenger land transport"),
    ("I","60.2E","Transports routiers de marchandises de proximité","Freight transport by road (short distance)"),
    ("I","60.2F","Transports routiers de marchandises à longue distance","Freight transport by road (long distance)"),
    ("I","60.2G","Déménagement","Removal services"),
    ("I","60.3Z","Transport par conduites","Transport via pipelines"),
    ("I","61.1A","Transports maritimes","Sea and coastal water transport"),
    ("I","61.1B","Transports côtiers","Coastal and inland waterway passenger water transport"),
    ("I","61.2Z","Transports fluviaux","Inland water transport"),
    ("I","62.1Z","Transports aériens réguliers","Scheduled air transport"),
    ("I","62.2Z","Transports aériens non réguliers","Non-scheduled air transport"),
    ("I","63.1A","Manutention portuaire","Cargo handling in ports"),
    ("I","63.1B","Manutention non portuaire","Other cargo handling"),
    ("I","63.1C","Entreposage frigorifique","Cold storage and warehousing"),
    ("I","63.1D","Entreposage non frigorifique","Other warehousing and storage"),
    ("I","63.2A","Gestion d'infrastructures de transport terrestre","Operation of land transport infrastructure"),
    ("I","63.2B","Gestion de ports","Services incidental to water transport"),
    ("I","63.2C","Gestion d'aéroports","Services incidental to air transport"),
    ("I","63.3Z","Agences de voyage","Activities of travel agencies"),
    ("I","63.4A","Messagerie, fret express","Courier activities other than national post activities"),
    ("I","63.4B","Affrètement","Freight transport brokerage"),
    ("I","63.4C","Organisation du transport international","Organisation of transport"),
    ("I","64.1A","Distribution et acheminement de courrier","Activities of post office"),
    ("I","64.1B","Autres activités de courrier","Other postal activities"),
    ("I","64.2A","Téléphonie et télégraphie","Wired telecommunications activities"),
    ("I","64.2B","Radiocommunication","Wireless telecommunications activities"),
    ("I","64.2C","Transmission par câble","Cable telecommunications activities"),
    ("I","64.2D","Autres activités de télécommunication","Other telecommunications activities"),

    # ── J — Activités financières ─────────────────────────────────────────────
    ("J","65.1A","Banque centrale","Central banking"),
    ("J","65.1B","Banques","Banking activities"),
    ("J","65.1C","Épargne-logement","Savings and mortgage institutions"),
    ("J","65.1D","Organismes de placement collectif","Collective investment activities"),
    ("J","65.1E","Crédit-bail","Financial leasing"),
    ("J","65.1F","Société financière","Other financial intermediation"),
    ("J","65.2A","Assurance-vie","Life insurance"),
    ("J","65.2B","Assurance dommages","Non-life insurance"),
    ("J","65.2C","Réassurance","Reinsurance"),
    ("J","66.0Z","Assurance","Insurance and pension funding"),
    ("J","66.0A","Assurance vie et capitalisation","Life insurance and capitalisation"),
    ("J","66.0B","Assurance dommages","Non-life insurance"),
    ("J","66.0C","Réassurance","Reinsurance"),
    ("J","67.1A","Administration de marchés financiers","Administration of financial markets"),
    ("J","67.1B","Courtage en valeurs mobilières","Security dealing on own account"),
    ("J","67.1C","Gestion de portefeuilles","Portfolio management"),
    ("J","67.2A","Auxiliaires d'assurance","Activities auxiliary to insurance and pension funding"),
    ("J","67.2B","Gestion de fonds de retraite","Pension fund management"),

    # ── K — Immobilier, locations et services aux entreprises ─────────────────
    ("K","70.1A","Promotion immobilière de logements","Development of building projects"),
    ("K","70.1B","Promotion immobilière de bureaux","Real estate activities with own or leased property"),
    ("K","70.1C","Promotion immobilière industrielle","Other real estate activities"),
    ("K","70.2Z","Location de biens immobiliers","Letting of own property"),
    ("K","70.3A","Agences immobilières","Real estate agencies"),
    ("K","70.3B","Administration d'immeubles résidentiels","Management of real estate on a fee or contract basis"),
    ("K","71.1Z","Location de véhicules automobiles","Renting of automobiles"),
    ("K","71.2A","Location d'autres moyens de transport terrestre","Renting of land transport equipment"),
    ("K","71.2B","Location de matériels de transport par eau","Renting of water transport equipment"),
    ("K","71.2C","Location de matériels de transport aérien","Renting of air transport equipment"),
    ("K","71.3A","Location de machines agricoles","Renting of agricultural machinery and equipment"),
    ("K","71.3B","Location de machines de construction","Renting of construction and civil engineering machinery"),
    ("K","71.3C","Location de machines de bureau","Renting of office machinery and equipment"),
    ("K","71.3E","Location d'autres machines","Renting of other machinery and equipment"),
    ("K","71.4Z","Location d'articles de loisirs et de sport","Renting of personal and household goods"),
    ("K","72.1Z","Conseil en systèmes informatiques","Hardware consultancy"),
    ("K","72.2A","Réalisation de logiciels","Software publishing"),
    ("K","72.2B","Conseil en applications informatiques","Software consultancy"),
    ("K","72.3Z","Traitement de données","Data processing"),
    ("K","72.4Z","Activités de bases de données","Database activities"),
    ("K","72.5Z","Entretien et réparation de machines de bureau","Maintenance and repair of office and accounting machinery"),
    ("K","72.6Z","Autres activités rattachées à l'informatique","Other computer related activities"),
    ("K","73.1Z","Recherche-développement en sciences physiques","Research and experimental development on natural sciences"),
    ("K","73.2Z","Recherche-développement en sciences humaines et sociales","Research and experimental development on social sciences"),
    ("K","74.1A","Activités juridiques","Legal activities"),
    ("K","74.1B","Activités comptables","Accounting, book-keeping and auditing activities"),
    ("K","74.1C","Activités de conseil de gestion","Management consultancy activities"),
    ("K","74.1D","Activités des holdings","Activities of holding companies"),
    ("K","74.1E","Administration d'entreprises","Business administration activities"),
    ("K","74.1F","Activités des sièges sociaux","Activities of head offices"),
    ("K","74.1G","Activités de contrôle et de certification","Testing and analysis activities"),
    ("K","74.2A","Activités d'architecture","Architectural activities"),
    ("K","74.2B","Métreurs, géomètres","Building inspection activities"),
    ("K","74.2C","Ingénierie","Engineering activities"),
    ("K","74.2D","Prospection minière","Technical testing and analysis"),
    ("K","74.2E","Ingénierie et études techniques","Other engineering activities"),
    ("K","74.3A","Analyses, essais et inspections techniques","Technical testing and analysis"),
    ("K","74.3B","Contrôle technique automobile","Motor vehicle testing"),
    ("K","74.4A","Conseil et assistance publicitaires","Advertising agencies"),
    ("K","74.4B","Régie publicitaire","Media representation"),
    ("K","74.5A","Sélection et mise à disposition de personnel","Labour recruitment and provision of personnel"),
    ("K","74.5B","Travail temporaire","Temporary employment agencies"),
    ("K","74.6Z","Enquêtes et sécurité","Investigation and security activities"),
    ("K","74.7A","Nettoyage courant des bâtiments","Building cleaning activities"),
    ("K","74.7B","Autres travaux de nettoyage","Other building and industrial cleaning activities"),
    ("K","74.8A","Studios et autres activités photographiques","Portrait photographic activities"),
    ("K","74.8B","Reproduction de documents","Photocopying, document preparation and other activities"),
    ("K","74.8C","Conditionnement à façon","Packaging activities"),
    ("K","74.8D","Secrétariat et traduction","Secretarial and translation activities"),
    ("K","74.8E","Routage","Mailing activities"),
    ("K","74.8F","Centres d'appels","Call centre activities"),
    ("K","74.8G","Administration d'autres affaires","Other business activities"),
    ("K","74.8H","Autres services aux entreprises","Other business services"),

    # ── L — Administration publique ───────────────────────────────────────────
    ("L","75.1A","Administration générale","General public administration activities"),
    ("L","75.1B","Administration publique (tutelle) de la santé","Regulation of the activities of health care"),
    ("L","75.1C","Administration publique (tutelle) de l'éducation","Regulation of educational activities"),
    ("L","75.1D","Administration publique (tutelle) des activités économiques","Regulation of and contribution to more efficient operation of businesses"),
    ("L","75.2A","Affaires étrangères","Foreign affairs"),
    ("L","75.2B","Défense","Defence activities"),
    ("L","75.2C","Justice","Justice and judicial activities"),
    ("L","75.2D","Activités de police","Public order and safety activities"),
    ("L","75.2E","Protection civile","Fire service activities"),
    ("L","75.3Z","Sécurité sociale obligatoire","Compulsory social security activities"),

    # ── M — Éducation ─────────────────────────────────────────────────────────
    ("M","80.1Z","Enseignement primaire","Primary education"),
    ("M","80.2A","Enseignement secondaire général","General secondary education"),
    ("M","80.2B","Enseignement secondaire technique ou professionnel","Technical and vocational secondary education"),
    ("M","80.3Z","Enseignement supérieur","Higher education"),
    ("M","80.4A","Écoles de conduite","Driving school activities"),
    ("M","80.4B","Formation continue d'adultes","Adult and other education"),

    # ── N — Santé et action sociale ───────────────────────────────────────────
    ("N","85.1A","Activités hospitalières","Hospital activities"),
    ("N","85.1B","Consultation et pratique médicale","Medical practice activities"),
    ("N","85.1C","Laboratoires d'analyses médicales","Other human health activities"),
    ("N","85.1D","Ambulances","Ambulance services"),
    ("N","85.1E","Autres activités pour la santé humaine","Other human health activities"),
    ("N","85.2Z","Activités vétérinaires","Veterinary activities"),
    ("N","85.3A","Crèches et garderies d'enfants","Child day-care activities"),
    ("N","85.3B","Hébergement médicalisé pour personnes âgées","Residential care activities for the elderly"),
    ("N","85.3C","Autres hébergements médicalisés","Other residential care activities"),
    ("N","85.3D","Aide par le travail, ateliers protégés","Sheltered workshop activities"),
    ("N","85.3E","Hébergement social pour adultes handicapés","Other residential care activities"),
    ("N","85.3F","Actions sociales sans hébergement","Social work activities without accommodation"),
    ("N","85.3G","Aide à domicile","Social work activities without accommodation for the elderly"),
    ("N","85.3H","Autres formes d'action sociale","Other social work activities without accommodation"),
    ("N","85.3J","Action sociale pour enfants","Child day-care activities"),

    # ── O — Services collectifs, sociaux et personnels ────────────────────────
    ("O","90.0A","Collecte et traitement des eaux usées","Sewage and refuse disposal, sanitation"),
    ("O","90.0B","Collecte et traitement des autres déchets","Collection and treatment of other waste"),
    ("O","90.0C","Décontamination et autres services de gestion des déchets","Decontamination and other waste management services"),
    ("O","91.1Z","Organisations patronales et consulaires","Activities of business, employers' and professional organisations"),
    ("O","91.2Z","Syndicats de salariés","Activities of trade unions"),
    ("O","91.3A","Organisations religieuses","Activities of religious organisations"),
    ("O","91.3B","Organisations politiques","Activities of political organisations"),
    ("O","91.3C","Organisations associatives diverses","Activities of other membership organisations"),
    ("O","91.3E","Activités d'organisations associatives diverses","Activities of other membership organisations"),
    ("O","92.1A","Production de films cinématographiques","Motion picture production activities"),
    ("O","92.1B","Production de programmes de télévision","Television programme production activities"),
    ("O","92.1C","Projection de films cinématographiques","Motion picture projection activities"),
    ("O","92.2A","Production de programmes de radio","Radio broadcasting activities"),
    ("O","92.2B","Diffusion de programmes de radio","Radio broadcasting distribution activities"),
    ("O","92.2C","Production de programmes de télévision","Television broadcasting activities"),
    ("O","92.2D","Diffusion de programmes de télévision","Television distribution activities"),
    ("O","92.3A","Représentations théâtrales","Performing arts"),
    ("O","92.3B","Autres représentations scéniques","Other performing arts"),
    ("O","92.3C","Manèges et parcs d'attractions","Fair and amusement park activities"),
    ("O","92.3D","Activités diverses du spectacle","Other entertainment activities"),
    ("O","92.4Z","Agences de presse","News agency activities"),
    ("O","92.5A","Gestion de bibliothèques","Library activities"),
    ("O","92.5B","Gestion de musées","Museum activities"),
    ("O","92.5C","Gestion de sites et monuments historiques","Operation of historical sites and buildings"),
    ("O","92.5D","Gestion du patrimoine naturel","Botanical and zoological gardens activities"),
    ("O","92.6A","Gestion d'installations sportives","Operation of sports facilities"),
    ("O","92.6B","Associations sportives et clubs","Activities of sport clubs"),
    ("O","92.6C","Autres activités sportives","Other sporting activities"),
    ("O","92.7A","Jeux de hasard et d'argent","Activities of gambling and betting establishments"),
    ("O","92.7C","Autres activités récréatives","Other recreational activities"),
    ("O","93.0A","Laveries-lavanderies","Laundering and dry-cleaning activities"),
    ("O","93.0B","Coiffure","Hairdressing and other beauty treatment"),
    ("O","93.0C","Soins de beauté","Beauty treatment activities"),
    ("O","93.0D","Soins aux personnes","Other service activities"),
    ("O","93.0E","Activités funéraires","Funeral and related activities"),
    ("O","93.0F","Autres soins corporels","Other personal service activities"),
    ("O","93.0G","Entretien corporel","Other personal service activities"),

    # ── P — Activités des ménages ─────────────────────────────────────────────
    ("P","95.0Z","Activités des ménages en tant qu'employeurs de personnel domestique","Activities of private households as employers of domestic staff"),
    ("P","96.0Z","Activités indifférenciées des ménages en tant que producteurs","Undifferentiated goods-producing activities of private households"),

    # ── Q — Activités extra-territoriales ─────────────────────────────────────
    ("Q","99.0Z","Activités extra-territoriales","Activities of extraterritorial organisations and bodies"),
]


class Command(BaseCommand):
    help = "Importe CategoryNafCode et SubCategoryNafCode — codes feuilles uniquement (regex ^\d{2}\.\d+[A-Z]$)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Affiche ce qui serait importé sans rien sauvegarder.")
        parser.add_argument("--clear", action="store_true",
                            help="Vide CategoryNafCode et SubCategoryNafCode avant l'import.")

    def handle(self, *args, **options):
        from main.models import CategoryNafCode, SubCategoryNafCode

        dry_run = options["dry_run"]
        clear   = options["clear"]

        # Filtrage strict : uniquement les vrais codes NAF feuilles
        leaf_codes = [(s, c, fr, en) for s, c, fr, en in NAF_CODES if NAF_LEAF_RE.match(c)]
        skipped_non_leaf = len(NAF_CODES) - len(leaf_codes)

        self.stdout.write(f"Catégories NAF         : {len(NAF_CATEGORIES)}")
        self.stdout.write(f"Codes NAF total        : {len(NAF_CODES)}")
        self.stdout.write(f"Codes non-feuilles ignorés : {skipped_non_leaf}")
        self.stdout.write(f"Codes feuilles à importer  : {len(leaf_codes)}")

        if dry_run:
            self._preview(leaf_codes)
            return

        with transaction.atomic():
            if clear:
                sub_n = SubCategoryNafCode.objects.count()
                cat_n = CategoryNafCode.objects.count()
                SubCategoryNafCode.objects.all().delete()
                CategoryNafCode.objects.all().delete()
                self.stdout.write(self.style.WARNING(
                    f"Tables vidées : {cat_n} catégorie(s), {sub_n} sous-catégorie(s)."
                ))

            # ── Étape 1 : Catégories ───────────────────────────────────────────
            cat_cache: dict[str, CategoryNafCode] = {}
            cat_created = cat_skipped = 0

            for code, libelle_fr, libelle_en, poids in NAF_CATEGORIES:
                cat, created = CategoryNafCode.objects.update_or_create(
                    code=code,
                    defaults={
                        "libelle":    libelle_fr,
                        "libelle_en": libelle_en,
                        "active":     True,
                        "poids":      poids,
                    },
                )
                cat_cache[code] = cat
                if created:
                    cat_created += 1
                else:
                    cat_skipped += 1

            self.stdout.write(
                f"Catégories : {cat_created} créée(s), {cat_skipped} mise(s) à jour."
            )

            # ── Étape 2 : Codes feuilles seulement ────────────────────────────
            sub_created = sub_skipped = sub_error = 0
            total = len(leaf_codes)

            for i, (section, code, libelle_fr, libelle_en) in enumerate(leaf_codes, 1):
                cat = cat_cache.get(section)
                if not cat:
                    sub_error += 1
                    self.stdout.write(self.style.ERROR(
                        f"  Catégorie '{section}' introuvable pour code '{code}'"
                    ))
                    continue

                sub, created = SubCategoryNafCode.objects.update_or_create(
                    code=code,
                    defaults={
                        "category":   cat,
                        "libelle":    libelle_fr,
                        "libelle_en": libelle_en,
                        "active":     True,
                        "poids":      cat.poids,
                    },
                )
                if created:
                    sub_created += 1
                else:
                    sub_skipped += 1

                if i % 100 == 0:
                    self.stdout.write(f"  {i}/{total} traités…")

            self.stdout.write(
                f"Codes NAF : {sub_created} créé(s), {sub_skipped} mis à jour, "
                f"{sub_error} erreur(s)."
            )

        self.stdout.write(self.style.SUCCESS("Import NAF terminé avec succès."))

    def _preview(self, leaf_codes):
        from collections import defaultdict
        grouped: dict[str, list] = defaultdict(list)
        for section, code, libelle_fr, libelle_en in leaf_codes:
            grouped[section].append((code, libelle_fr, libelle_en))

        self.stdout.write("\n--- PREVIEW (dry-run) ---")
        for section, libelle_fr, libelle_en, _ in NAF_CATEGORIES:
            codes = grouped.get(section, [])
            self.stdout.write(
                f"\n[CAT] {section} — {libelle_fr} / {libelle_en} ({len(codes)} codes)"
            )
            for code, fr, en in codes[:3]:
                self.stdout.write(f"  {code:10} FR: {fr[:50]}")
                self.stdout.write(f"           EN: {en[:50]}")
            if len(codes) > 3:
                self.stdout.write(f"  ... +{len(codes)-3} autres")
        self.stdout.write(
            f"\nTotal : {len(NAF_CATEGORIES)} catégories, {len(leaf_codes)} codes feuilles."
        )
