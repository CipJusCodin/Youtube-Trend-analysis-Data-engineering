# 🚀 Serverless YouTube Trending Data Analytics Platform on AWS

## Project Overview
This project establishes a resilient, **end-to-end data pipeline** on **Amazon Web Services (AWS)** to ingest, clean, transform, and analyze a large dataset of trending YouTube videos. It models a modern data platform by building a **Medallion Architecture (Raw, Cleansed, Analytics)** on an S3-based Data Lake.

The primary goal is to handle disparate data formats (CSV for statistics, nested JSON for metadata) and consolidate them into a fast, queryable **analytical layer** to derive insights, such as understanding the factors that drive video popularity across different global regions.

---

## 💾 Data Source and Schema Details
### Data Source
The data is sourced from the **Kaggle YouTube Trending Videos Dataset**, which compiles daily statistics for trending videos across multiple international regions.

🔗 **Dataset Link:** [https://www.kaggle.com/datasets/datasnaek/youtube-new?resource=download](https://www.kaggle.com/datasets/datasnaek/youtube-new?resource=download)

### Raw Dataset Schema

The pipeline processes two primary types of files:

#### 1. Video Statistics Data (CSV Files)
This raw data is separated by region (e.g., `USvideos.csv`, `CAvideos.csv`).

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `video_id` | String | Unique identifier for the YouTube video. **(Primary Key / Join Key)** |
| `trending_date` | Date | Date the video was listed as trending. |
| `title` | String | Video title. |
| `channel_title` | String | Name of the publishing channel. |
| `category_id` | Integer | ID linking to the category reference data. **(Foreign Key / Join Key)** |
| `publish_time` | Timestamp | Date and time the video was published. |
| `views` | Integer | Number of views. |
| `likes` | Integer | Number of likes. |
| `comment_count`| Integer | Number of comments. |
| `description` | String | Full video description. |

#### 2. Category Reference Data (JSON Files)
This semi-structured data is used as a lookup table and must be flattened during the transformation process.

| Column Name | Raw JSON Structure | Description |
| :--- | :--- | :--- |
| `kind` | String | Resource type (e.g., "youtube#videoCategoryList"). |
| `etag` | String | Entity tag for the resource. |
| `items` | Array of Objects | **Nested data structure** containing the list of categories. |
| `id` (Flattened) | BigInt | The category ID (e.g., `1`, `10`, `22`). |
| `snippet.title` (Flattened) | String | The human-readable category name (e.g., "Film & Animation", "Music"). |

---

## 🗺️ Project Architecture and Data Flow
The architecture follows a serverless Data Lakehouse pattern, ensuring data is stored cost-effectively while remaining highly queryable.



[Image of AWS Data Lake Architecture]


### Data Flow Stages:

1.  **Ingestion (S3 Raw Layer):** Data is uploaded using the AWS CLI into the raw S3 bucket, partitioned by file type (CSV vs. JSON) and region.
2.  **JSON Pre-Processing (Lambda ETL):**
    * **Automation:** An **S3 Put event trigger** invokes an **AWS Lambda** function whenever a new JSON file arrives.
    * **Transformation:** The Lambda function (Python/Pandas/AWS Wrangler) reads the file, flattens the nested `items` array, applies necessary schema fixes (e.g., casting `id` to **BigInt**), and writes the output as **Parquet** to the Cleansed Layer.
3.  **Structured Transformation (Glue ETL) with Optimization:**
    * An **AWS Glue ETL Job** is created and run using a PySpark script.
    * **Crucial Optimization: The cleansed data is partitioned by `region` (`partition_keys=['region']`) when writing to S3.** This drastically reduces the data scanned by Athena, lowering query costs and latency.
    * **Filtering:** A **predicate pushdown** is implemented to select only target regions (US, CA, GB) for initial pipeline stability.
    * **Conversion:** The job reads the raw CSVs, converts the data types, and writes the output as optimized **Parquet** to the Cleansed Layer.
4.  **Analytical Layer (Glue Studio Job):**
    * A final **Glue Studio** visual job performs an **INNER JOIN** between the Cleansed CSV data and the Cleansed JSON category data on the `category_id` column.
    * This **denormalized** analytical dataset is written to the `Analytics` S3 bucket, **further partitioned by `region` and `category_id`**, making it highly optimized for BI reporting.
5.  **Reporting & Insights:**
    * **Amazon Athena** is used to query the final analytical table using standard SQL, leveraging the S3 partitioning for efficient data access.
    * **Amazon QuickSight** connects to Athena to visualize key performance indicators (KPIs) like total views, most popular categories, and regional trending patterns.

---

## 🛠️ AWS Services and Rationale
The project maximizes the use of serverless, managed services to minimize operational overhead and ensure scalability.

| Service | Category | Purpose in Project | Rationale |
| :--- | :--- | :--- | :--- |
| **Amazon S3** | Storage (Data Lake) | Used to implement the **Raw**, **Cleansed**, and **Analytics** zones of the Data Lake architecture. | **Serverless, 99.999999999% Durability,** and **Tiered Storage** (cost-effective long-term storage). |
| **AWS Glue** | ETL & Catalog | Used for **ETL processing** (including **partitioning**) and for **metadata management** (**Glue Data Catalog**). | **Managed PySpark Environment.** Handles large-scale data transformation and efficiently organizes data in S3. |
| **AWS Lambda** | Compute/Automation | Used for the **event-driven ETL** necessary to normalize the semi-structured JSON reference data. | **Zero-Server Management** for bursty, small compute tasks. |
| **Amazon Athena**| Querying/Ad-Hoc | Used for **interactive, serverless SQL queries** directly against Parquet files in S3. | **Pay-per-query model.** Partitioning ensures only relevant data is scanned, significantly reducing cost. |
| **Amazon QuickSight**| Business Intelligence | Used to build the final **analytical dashboard** based on the structured data in the Analytics layer. | **Cloud-Native BI.** Provides a fully managed platform for visualization. |
| **AWS IAM** | Security | Used to define and apply **least-privilege access roles** for all services (Glue, Lambda, Athena) to interact with S3 buckets. | **Granular and Secure Access Control.** |

---
