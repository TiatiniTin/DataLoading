import ee
import datetime

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
geom = ee.Geometry.Polygon([[45.8777, 45.4055],
                            [45.8777, 45.3657],
                            [45.9501, 45.3657],
                            [45.9501, 45.4055]])

# Call collection of satellite images.
collection = (ee.ImageCollection('COPERNICUS/S2_SR')
              # Select the Red, Green and Blue image bands, as well as the cloud masking layer.
              .select(['B4', 'B3', 'B2', 'QA60'])
              # Filter for images within a given date range.
              .filter(ee.Filter.date('2017-07-01', '2017-10-31'))
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
today = datetime.datetime.today()
task_config = {
    'region': geom.coordinates().getInfo(),
    'folder': 'Santinel',
    'scale': 10,
    'crs': 'EPSG:4326',
    'description': 'Example_File_Name' + today.strftime("%Y-%m-%d-%H.%M.%S")
}

# Export Image
task = ee.batch.Export.image.toDrive(image, **task_config)
task.start()