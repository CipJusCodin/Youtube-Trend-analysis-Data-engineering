# NOTE: Update the following values for your environment:
# - S3 bucket: s3://de-youtube-reccomendation-cleaned-data/
# - Database: de-youtube-raw
# - Table: raw_statistics


import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Filter for specific regions only (performance optimization)
predicate_pushdown = "region in ('ca','gb','us')"

# Read from Glue Catalog with filter
datasource0 = glueContext.create_dynamic_frame.from_catalog(
    database="de-youtube-raw", 
    table_name="raw_statistics", 
    transformation_ctx="datasource0", 
    push_down_predicate=predicate_pushdown
)

# Apply schema mapping
applymapping1 = ApplyMapping.apply(
    frame=datasource0, 
    mappings=[
        ("video_id", "string", "video_id", "string"), 
        ("trending_date", "string", "trending_date", "string"), 
        ("title", "string", "title", "string"), 
        ("channel_title", "string", "channel_title", "string"), 
        ("category_id", "long", "category_id", "long"),  # long = bigint
        ("publish_time", "string", "publish_time", "string"), 
        ("tags", "string", "tags", "string"), 
        ("views", "long", "views", "long"), 
        ("likes", "long", "likes", "long"), 
        ("dislikes", "long", "dislikes", "long"), 
        ("comment_count", "long", "comment_count", "long"), 
        ("thumbnail_link", "string", "thumbnail_link", "string"), 
        ("comments_disabled", "boolean", "comments_disabled", "boolean"), 
        ("ratings_disabled", "boolean", "ratings_disabled", "boolean"), 
        ("video_error_or_removed", "boolean", "video_error_or_removed", "boolean"), 
        ("description", "string", "description", "string"), 
        ("region", "string", "region", "string")
    ], 
    transformation_ctx="applymapping1"
)

# Resolve any choice types (handles ambiguous types)
resolvechoice2 = ResolveChoice.apply(
    frame=applymapping1, 
    choice="make_struct", 
    transformation_ctx="resolvechoice2"
)

# Drop null fields to clean data
dropnullfields3 = DropNullFields.apply(
    frame=resolvechoice2, 
    transformation_ctx="dropnullfields3"
)

# Coalesce to 1 file per partition (combines small files)
datasink1 = dropnullfields3.toDF().coalesce(1)
df_final_output = DynamicFrame.fromDF(datasink1, glueContext, "df_final_output")

# Write to S3 with partitioning by region
datasink4 = glueContext.write_dynamic_frame.from_options(
    frame=df_final_output, 
    connection_type="s3", 
    connection_options={
        "path": "s3://de-youtube-reccomendation-cleaned-data/youtube/raw_statistics/", 
        "partitionKeys": ["region"]
    }, 
    format="parquet", 
    transformation_ctx="datasink4"
)

job.commit()
