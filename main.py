import ee

ee.Authenticate()

# Initialize the library.
ee.Initialize()


# This is the cloud masking function provided by GEE but adapted for use in Python.
def maskS2clouds(image):
    qa = image.select('QA60')

    # Bits 10 and 11 are clouds and cirrus, respectively.
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11

    # Both flags should be set to zero, indicating clear conditions.
    mask = qa.bitwiseAnd(cloudBitMask).eq(0)
    mask = mask.bitwiseAnd(cirrusBitMask).eq(0)

    return image.updateMask(mask).divide(10000)


# Define the geometry of the area for which you would like images.
# geom = ee.Geometry.Polygon([[34.8777, -13.4055],
#                     [34.8777, -13.3157],
#                        [34.9701, -13.3157],
#                     [34.9701, -13.4055]])

# geom1 = ee.Geometry.Rectangle([40.44278139887932,40.46192258314811,87.72793764887932,55.63910542055555])
geom = ee.Geometry.Polygon([[41.23379702387932, 55.327254680594635],
                            [41.23379702387932, 40.24345594801423],
                            [90.18887514887932, 40.24345594801423],
                            [90.18887514887932, 55.327254680594635]])

# geom1 = ee.Geometry.Polygon([[40.44278139887932, 40.46192258314811],
#                            [87.72793764887932, 40.46192258314811],
#                           [87.72793764887932, 55.63910542055555],
#                          [40.44278139887932, 55.63910542055555]])


# Call collection of satellite images.
collection = (ee.ImageCollection("COPERNICUS/S2_SR")
              # Select the Red, Green and Blue image bands, as well as the cloud masking layer.
              .select(['B4', 'B3', 'B2', 'QA60'])
              # Filter for images within a given date range.
              .filter(ee.Filter.date('2017-01-01', '2017-03-31'))
              # Filter for images that overlap with the assigned geometry.
              .filterBounds(geom)
              # Filter for images that have less then 20% cloud coverage.
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
              # Apply cloud mask.
              .map(maskS2clouds)
              )

# Sort images in the collection by index (which is equivalent to sorting by date),
# with the oldest images at the front of the collection.
# Convert collection into a single image mosaic where only images at the top of the collection are visible.
image = collection.sort('system:index', opt_ascending=False).mosaic()

# Assign visualization parameters to the image.
image = image.visualize(bands=['B4', 'B3', 'B2'],
                        min=[0.0, 0.0, 0.0],
                        max=[0.3, 0.3, 0.3]
                        )

# Assign export parameters.
task_config = {
    'region': geom.coordinates().getInfo(),
    'folder': 'new',
    'scale': 100,
    'crs': 'EPSG:4326',
    'description': 'test_14_6'
}

# Export Image
task = ee.batch.Export.image.toDrive(image, **task_config)
task.start()
