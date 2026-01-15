README – Kappa IoT: Strumieniowa analiza danych z czujników

1. Opis projektu
Projekt Kappa IoT realizuje potok danych w architekturze Kappa, który w czasie rzeczywistym przetwarza dane z czujników IoT. Dane przechodzą z Azure Event Hubs do Azure Databricks, gdzie są przetwarzane w celu obliczenia agregatów temperatury i wykrywania anomalii. Wyniki są zapisywane w Delta Lake i udostępniane jako prosty dashboard.

Usługi użyte w projekcie:
- Azure Event Hub (input-stream) w namespace event-hubs-ns-ns
- Azure Databricks Workspace (databrick) z notebookami notebook i capstone-pipeline
- Azure Data Lake Storage (iadoutputstoragens) z mount point /mnt/delta-output
- Terraform do automatycznego tworzenia infrastruktury
- GitHub Actions (CI/CD) – opcjonalnie do deploymentu notebooków
- Azure Monitor do logów i metryk

2. Struktura repozytorium 
kappa-iot/
├── README.md
├── send_events.py           #Symulator wysyłający dane do Event Hub
├── notebooks/
│   ├── notebook.ipynb       #Mounty i konfiguracja środowiska
│   └── capstone-pipeline.ipynb #Strumieniowe przetwarzanie i zapis do Delta Lake
└── terraform/
    ├── main.tf              #Definicja Resource Group, Storage, Event Hub, Databricks
    └── variables.tf         #Opcjonalne zmienne


3. Wdrożenie infrastruktury (Terraform)
3.1 Zaloguj się do Azure CLI:
az login
3.2 Prezjdź do katalogug Terraform
cd terraform
3.3 Zainicjalizuj Terraform
terraform init
3.4 Sprawdź plan wdrożenia
terraform plan
3.5 Zastosuj konfigurację
terraform apply
# Potwierdź wpisując 'yes'

Po wykonaniu powyższych kroków zostaną utworzone:
- Resource Group iad-lab-rg
- Storage Account iadoutputstoragens z mount point /mnt/delta-output
- Event Hub Namespace event-hubs-ns-ns i Event Hub input-stream

4. Tworzenie DataBrick Workspce
Azure Databricks Workspace w projekcie nie jest tworzony przez Terraform i został utworzony ręcznie w Azure Portal, zgodnie z wymaganiami zajęć.

Kroki utworzenia Databricks Workspace:
4.1 Zaloguj się do Azure Portal: https://portal.azure.com
4.2 Wybierz Create a resource → Analytics → Azure Databricks
4.3 Ustaw parametry:
- Workspace name: databrick
- Subscription: Azure for Students
- Resource Group: iad-lab-rg
- Region: West Europe
- Pricing tier: Standard (lb Wersja próbna, jeśli dostępna)
4.4 Kliknij Review + Create, a następnie Create
4.5 Po zakończeniu wdrażania przejdź do utworzonego workspace i uruchom obszar roboczy

5. Dodanie bibliotek klastra
Przejdź do zakładki "Compute", następnie wybierz klaster. Przejdź do zakładki "Libraries". Kliknij "Install new". Wybierz library Source "Maven", wklej poniższą linijkę  w odpowiednie miejsce:
com.microsoft.azure:azure-eventhubs-spark_2.12:2.3.22

6. Utwórz notebook:
6.1 Notebook "Notebook1"
Notebook odpowiedzialny za:
- konfigurację połączenia z Azure Data Lake Storage,
- utworzenie mount points.

Kod wklej do komórki notebooka, w miejsca "TWOJ_KLUCZ", "TWOJ_ACCESS_KEY" wpisując odpowiednie klucze dostępu z platformy azure:

storage_account_name = "iadoutputstoragensprojekt"
storage_account_access_key = "TWOJ_KLUCZ"
container_name = "delta-output"
mount_point = "/mnt/delta-output"

dbutils.fs.mount(
  source = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net",
  mount_point = mount_point,
  extra_configs = {f"fs.azure.account.key.{storage_account_name}.blob.core.windows.net": storage_account_access_key})

storage_account_name = "iadoutputstoragens"
storage_account_access_key = "TWOJ_ACCESS_KEY"
container_name = "checkpoints"
mount_point = "/mnt/checkpoints"

dbutils.fs.mount(
  source = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net",
  mount_point = mount_point,
  extra_configs = {f"fs.azure.account.key.{storage_account_name}.blob.core.windows.net": storage_account_access_key})

6.2 Uruchom komórkę.

7. Uruchom plik send_events.py

8. Utwórz Notebook "capstone-pipeline"
Notebook realizujący główną logikę potoku danych:
- odczyt strumienia z Azure Event Hub (input-stream),
- przetwarzanie danych w Apache Spark Structured Streaming,
- agregacje w oknach czasowych z watermarkami,
- zapis wyników do Delta Lake,
- checkpointing umożliwiający wznowienie przetwarzania.

Kod wklej do trzech kolejnych komórek notatnika:
1) 
from pyspark.sql.functions import (
    from_json, col, window, avg, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType
)

schema = StructType([
    StructField("deviceId", StringType(), True),
    StructField("temperature", DoubleType(), True),
    StructField("humidity", DoubleType(), True),
    StructField("pressure", DoubleType(), True),
    StructField("timestamp", StringType(), True)   # STRING → potem konwersja
])

connectionString = "TWOJ_KLUCZ"
ehConf = {
  'eventhubs.connectionString' : spark._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(connectionString),
  'eventhubs.eventHubName': 'input-stream'
}

# Odczyt strumienia
inputStreamDF = spark.readStream.format("eventhubs").options(**ehConf).load()




jsonStreamDF = (
    inputStreamDF
        .select(from_json(col("body").cast("string"), schema).alias("data"))
        .select("data.*")
        .withColumn(
            "event_time",
            to_timestamp(col("timestamp"))  # ISO 8601 → TimestampType
        )
        .drop("timestamp")
)



# Agregacja: średnia temperatura w 30-sekundowym oknie
avgTempDF = (
    jsonStreamDF
        .withWatermark("event_time", "1 minute")
        .groupBy(
            window(col("event_time"), "30 seconds"),
            col("deviceId")
        )
        .agg(
            avg("temperature").alias("avg_temperature"),
            avg("humidity").alias("avg_humidity"),
            avg("pressure").alias("avg_pressure")
        )
)






######################################
2) # Zapis do Delta Lake
query = (
    avgTempDF.writeStream
        .format("delta")
        .outputMode("append")
        .option("path", "/mnt/delta-output/iot_aggregates")
        .option("checkpointLocation", "/mnt/checkpoints/iot_aggregates")
        .start()
)




#############################3#######
3)
from pyspark.sql.functions import when

anomaliesDF = (
    jsonStreamDF
        .withColumn(
            "is_anomaly",
            when(col("temperature") > 40, True).otherwise(False)
        )
        .filter(col("is_anomaly") == True)
)

anomalyQuery = (
    anomaliesDF.writeStream
        .format("delta")
        .outputMode("append")
        .option("path", "/mnt/delta-output/iot_anomalies")
        .option("checkpointLocation", "/mnt/checkpoints/iot_anomalies")
        .start()
)

########################
8.1 Uruchom wszytskie komórki

9.	Po kilku minutach działania potoku, zatrzymaj go. Dane są teraz trwale zapisane w Twoim Data Lake. 

10. Utwórz kolejny notebook, w którym dane zapisywane są do tabeli. W tym celu do komórki wklej poniższy kod:
resultsDF = spark.read.format("delta").load("/mnt/delta-output/iot_aggregates")

display(
    resultsDF
        .select(
            "window.start",
            "window.end",
            "deviceId",
            "avg_temperature",
            "avg_humidity",
            "avg_pressure"
        )
        .orderBy("start", "deviceId")
)

11. Wybierz opcję "Download CSV" -> "All rows".

12. Dane mogą zostać wyeksportowane do PowerBI i zwizualizowane.
