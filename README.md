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
This data contains the core metrics and video metadata, as shown in the provided spreadsheet image.

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `video_id` | String | Unique identifier for the YouTube video. |
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
This semi-structured data is used as a lookup table and requires **flattening** to be usable.

| Column Name | Raw JSON Structure | **Transformation** | Description |
| :--- | :--- | :--- | :--- |
| **Root Payload** | `{ "items": [ ... ] }` | The **AWS Lambda** ETL must extract and iterate through the **nested `items` array**. | The array contains the full list of video categories. |
| `id` | `items[*].id` | **Extracted Column** | The numerical category ID, used to join with the CSV data. |
| `title` | `items[*].snippet.title` | **Extracted Column** | The human-readable category name (e.g., "Music," "Sports"). |

---

## 🗺️ Project Architecture and Data Flow
The architecture follows a serverless Data Lakehouse pattern, ensuring data is stored cost-effectively while remaining highly queryable.


### Data Flow Stages:

1.  **Ingestion (S3 Raw Layer):** Data is uploaded using the AWS CLI into the raw S3 bucket, partitioned by file type (CSV vs. JSON) and region.
2.  **JSON Pre-Processing (Lambda ETL):**
    * **Automation:** An **S3 Put event trigger** invokes an **AWS Lambda** function whenever a new JSON file arrives.
    * **Transformation:** The Lambda function (Python/Pandas/AWS Wrangler) reads the file, **flattens the nested `items` array**, applies necessary schema fixes (e.g., casting `id` to **BigInt**), and writes the output as **Parquet** to the Cleansed Layer.
3.  **Structured Transformation (Glue ETL) with Optimization:**
    * An **AWS Glue ETL Job** is created and run using a PySpark script.
    * **Crucial Optimization:** The output data is explicitly **partitioned by `region` (`partition_keys=['region']`) when writing the Parquet files to S3.** This drastically reduces the data scanned by Athena, lowering query costs and latency.
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
