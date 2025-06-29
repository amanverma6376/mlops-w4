from datetime import timedelta
from feast import Entity, FeatureView, Field, ValueType  
from feast.types import Float32, Int64, String
from feast import BigQuerySource

iris_entity = Entity(
    name="iris_entity",
    join_keys=["iris_entity_id"]
)

iris_source = BigQuerySource(
    table="citric-aleph-461515-j9.iris_dataset.iris_table",
    timestamp_field="event_timestamp",
    value_type=ValueType.INT64,
)

iris_feature_view = FeatureView(
    name="iris_features",
    entities=[iris_entity],  
    ttl=timedelta(days=365),
    schema=[
        Field(name="sepal_length", dtype=Float32),
        Field(name="sepal_width", dtype=Float32),
        Field(name="petal_length", dtype=Float32),
        Field(name="petal_width", dtype=Float32),
        Field(name="species", dtype=String),
    ],
    online=True,
    source=iris_source, 
)
