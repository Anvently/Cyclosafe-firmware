Contient des scripts et utilitaires destinés à faciliter la récupération des données.

- [gpx\_exporter.py](#gpx_exporterpy)
  - [Usage](#usage)
  - [Exemple](#exemple)
  - [Paramètres](#paramètres)
- [import\_recordings.py](#import_recordingspy)
  - [Usage](#usage-1)
  - [Exemple](#exemple-1)
  - [Paramètres](#paramètres-1)
  - [Procédure normale](#procédure-normale)
  - [Documentation et suppléments sur rosbag](#documentation-et-suppléments-sur-rosbag)

# gpx_exporter.py

Permet d'exporter les données GPS contenues dans un rosbag vers un format gpx.

## Usage

~~~
$ python3 ./gpx_exporter.py --help
usage: gpx_exporter.py [-h] -b BAG [-o OUTPUT_PATH] [-n NAME]

Extrait les données GPS d'un bag ROS2 et les exporte au format GPX

options:
  -h, --help            show this help message and exit
  -b BAG, --bag BAG     Chemin vers le fichier bag ROS2 (.mcap)
  -o OUTPUT_PATH, --output-path OUTPUT_PATH
                        Chemin du fichier GPX de sortie
  -n NAME, --name NAME  Nom personnalisé pour la trace GPS
~~~

## Exemple

~~~
$ python3 ./gpx_exporter.py -b ~/data/20250513-064355/out/_0.mcap
[16:49:01] INFO     Traitement terminé. 24 points GPS extraits et enregistrés dans                 gpx_exporter.py:173
                    /home/npirard/data/20250513-064355/out/trace.gpx   
~~~

## Paramètres

> **-b (--bag)**
> 	- **obligatoire**
> 	- chemin vers le bag à partir duquel extraire les données gps

> **-o (--output-path)**
> 	- **optionnel**
> 	- chemin de sortie pour la trace gpx
> 	- si non indiqué, elle sera enregistrée dans le même répertoire que le bag

> **-n (--name)**
> 	- **optionnel**
> 	- nom de la trace gpx (il ne s'agit pas du nom du fichier mais bien de la trace)

# import_recordings.py

Utilitaire permettant :
- d'exporter l'ensemble des enregistrement d'un raspberry via ssh
- de décompresser les bags et de les convertir en fichiers uniques
- de réparer les éventuels enregistrements corrompus

Il est nécessaire de préciser l'une des deux options d'import (**-u** en ssh ou **-c** pour une copie).

## Usage

~~~
$ ./import_recordings.py --help
usage: import_recordings.py [-h] [-u HOSTNAME] [-c COPY] [-s SKIP_IMPORT] [-o OUTPUT]

Import and convert rosbag files from a remote host.

options:
  -h, --help            show this help message and exit
  -u HOSTNAME, --hostname HOSTNAME
                        Hostname for SSH connection (user@host-ip)
  -c COPY, --copy COPY  Path to a local source directory (e.g., mounted SD card) to copy from
  -s SKIP_IMPORT, --skip_import SKIP_IMPORT
                        Skip import step and use specified local path for conversion
  -o OUTPUT, --output OUTPUT
                        Output directory for imported bags

~~~

## Exemple

~~~
./import_recordings.py -u npirard@192.168.2.2 -o ~/data/test/
~~~

Résultat
~~~
           INFO     Output directory: /home/npirard/data/test                 
Enter SSH password: 
           INFO     Retrieving record list from npirard@192.168.2.2...         
           INFO     Found 9 record directories.                                
           INFO     [1/9] Importing 20250515-125430 to /home/npirard/data/test...
           INFO     Running: sshpass -p XXXX scp -r                        
                    npirard@192.168.2.2:/home/npirard/data/20250515-125430                                            
                    /home/npirard/data/test/        
...
INFO     [2/8] Converting bags in 20250515-125326...                       
           WARNING  /home/npirard/data/test/20250515-125326 is missing a metadata.yaml
Attempting to repair /home/npirard/data/test/20250515-125326/bag
           INFO     Running: unzstd
                    /home/npirard/data/test/20250515-125326/bag/bag_0.mcap.zstd
           INFO     Successfully uncompressed bag
           INFO     Running: ros2 bag reindex .
...
           INFO     All operations completed successfully! 
~~~

**Pour convertir/réparer seulement les données** :

~~~
./import_recordings.py -s ~/data/test/
~~~

Résultat

~~~
INFO     Output directory: /home/npirard/data/pouet                                import_recordi:246
           INFO     Found 8 record directories in /home/npirard/data/test
           INFO     [1/8] Converting bags in 20250516-175032...
           INFO     Converted bag already exist in /home/npirard/data/test/20250516-175032,
                    skipping...                                
...
           INFO     All operations completed successfully!
~~~

## Paramètres

> **-u (--hostname)**
> 	- **optionnel**
> 	- adresse ssh au format **user@ip** du raspberry à joindre
> 	- le répertoire à partir duquel importer les enregistrement sera **user@ip:/home/user/data/**

> **-c (--copy)**
> 	- **optionnel**
> 	- chemin local à partir duquel les enregistrements
> 	- **Ex:** /media/sdcard0/home/user/data

> **-o (--output-path)**
> 	- **optionnel**
> 	- **par défaut** : ~/data/import
> 	- chemin auquel importer les données sur l'host

> **-s (--skip-import)**
> 	- **optionnel**
> 	- Ignore la phase d'import
> 	- Convertit seulement les données en réparant les éventuelles corruptions


## Procédure normale

1. les enregistrements sont importés tels quel (en gardant leur strucutre) dans le dossier précisé par l'option **-o** (ou **~/data/import** si non précisé).

	Cela peut-être fait via ssh avec l'option **-u** ou par copie depuis une carte sd avec l'option **-c**.
	
	La structure d'un enregistrement importé est la suivante :
	~~~
	$ tree ~/data/
	/home/npirard/data/
	└── 20250515-125326 # Date de l'enregistrement
		├── bag # Dossier contenant les fichiers créés par rosbag
		│   ├── bag_0.mcap.zstd
		│   ├── bag_1.mcap.zstd
		│   └── metadata.yaml
		└── logs # Un fichier log pour chaque noeud
		    ├── ldlidar_stl_ros2_node_1008_1747313607000.log
		    ├── node_lidar_1087_1747313611560.log
		    ├── python3_1002_1747313608450.log
		    ├── python3_1004_1747313613884.log
		    ├── python3_1006_1747313608700.log
		    └── rplidar_node_1010_1747313607000.log
	~~~
2. pour chaque enregistrement, les bags morcelés en plusieurs fichiers sont réunis en un seul fichier non compressé au format **.mcap** dans un nouveau sous-dossier **out/**.

   Les bags compressés sont décompressés au passage.

   Cela est fait via la commande suivante :
   ~~~
   ros2 bag convert -i /home/npirard/data/20250515-125326/bag -o /home/npirard/data/20250515-125326/out/out_options
   ~~~

   Le fichier **out_options** dont il est question défini les paramètres de sortie de la conversion, notamment le nom de sortie du bag converti.

   Voici son contenu :
   ~~~
   output_bags:
   - uri: ./out/  # required
     storage_id: ""  # will use the default storage plugin, if unspecified
     max_bagfile_size: 0
     max_bagfile_duration: 0
     storage_preset_profile: ""
     storage_config_uri: ""
     # optional filter for msg time t [nsec since epoch]:  start_time_ns <= t <= end_time_ns
     # start_time_ns: 1744227144744197147
     # end_time_ns: 1744227145734665546
     all_topics: true # may be used as a filter
     topics: []
     topic_types: []
     all_services: true
     services: []
     all_actions: true
     actions: []
     rmw_serialization_format: ""  # defaults to using the format of the input topic
     regex: ""
     exclude_regex: ""
     exclude_topics: []
     exclude_topic_types: []
     exclude_services: []
     exclude_actions: []
     compression_mode: ""
     compression_format: ""
     compression_queue_size: 1
     compression_threads: 0
     include_hidden_topics: false
     include_unpublished_topics: false
     ~~~

3. On doit obtenir à la fin la structure suivante :
	~~~
	$ tree ~/data/
	/home/npirard/data/
	└── 20250515-125326 # Date de l'enregistrement
		├── bag # Dossier contenant les fichiers créés par rosbag
		│   ├── bag_0.mcap.zstd
		│   ├── bag_0.mcap
		│   ├── bag_1.mcap.zstd
		│   ├── bag_1.mcap
		│   └── metadata.yaml
		├── logs
		│   ├── ldlidar_stl_ros2_node_1008_1747314778850.log
		│   ├── node_lidar_1087_1747314783363.log
		│   ├── python3_1002_1747314780257.log
		│   ├── python3_1004_1747314785384.log
		│   ├── python3_1006_1747314780497.log
		│   └── rplidar_node_1010_1747314778850.log
		├── out # Dossier de sortie du bag converti
		│   ├── _0.mcap # Contient l'intégralité de l'enregistrement
		│   └── metadata.yaml # Information sur l'enregistrement
		└── out_options
	~~~

Techniquement, un fichier **.mcap** contient déjà une bonne partie des informations de **metadata.yaml** et peut-être utilisé indépendant du fichier metadata associé.

Par exemple, [**cyclosafe_player**](../viewer/cyclosafe_player/README.md) prend seulement un fichier **.mcap** (compressé ou non) en entrée.

Cependant de nombreux outils de ROS2 (notamment la suite **rqt**) prennent en paramètre le dossier contenant le bag et s'attendent donc à ce que ce dossier contienne également un fichier **metadata.yaml**.

## Réparation des corruptions

Lorsque le raspberry s'éteint brutalement ou que [**cyclosafed.service**](../core/setup/systemd/README.md#cyclosafedservice) n'a pas le temps de se fermer correctement, les enregistrements peuvent être corrompus. Dans ce cas il faut s'attendre à la situation suivante :

- le dernier fichier .mcap (celui en cours d'écritureau moment de l'arrêt) n'est pas compressé (.mcap au lieu .mcap.zstd)
- une corruption possible du fichier .mcap en cours d'écriture (vérifiable avec **ros2 bag info ***chemin_du_dossier_bag*****)
- une absence du fichier **metadata.yaml** qui contient les métadonnées sur le bag et qui référence l'ensemble des différents fichiers .mcap (compressés ou non).

<ins>**Exemple**</ins> :
~~~
$ tree ~/data/20250515-125326
/home/npirard/data/20250515-125326
├── bag # Absence du fichier metadata.yaml
│   ├── bag_0.mcap.zstd
│   └── bag_1.mcap # Le dernier bag n'est pas compressé
└── logs
    ├── ldlidar_stl_ros2_node_1008_1747313607000.log
    ├── node_lidar_1087_1747313611560.log
    ├── python3_1002_1747313608450.log
    ├── python3_1004_1747313613884.log
    ├── python3_1006_1747313608700.log
    └── rplidar_node_1010_1747313607000.log
~~~

Le script détecte les corruptions par l'absence du fichier metadata.yaml et entreprend alors de les réparer automatiquement.

La procédure est la suivante :

1. Décompresse les bags qui sont compressés
   ~~~
   unzstd ~/data/20250515-125326/bag/*.zstd
   ~~~
2. Reconstruit le fichier metadata (certains warning peuvent apparaître)
   ~~~
   ros2 bag reindex ~/data/20250515-125326/bag
   ~~~
3. A partir de de là, on peut suivre l'étape normale de la conversion

## Documentation et suppléments sur rosbag

https://github.com/ros2/rosbag2?tab=readme-ov-file#rosbag2