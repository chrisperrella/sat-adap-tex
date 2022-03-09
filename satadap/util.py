def blank_image( output_path, resolution ):
    import numpy, cv2
    image = numpy.zeros( ( resolution, resolution, 3 ) )
    cv2.imwrite( str( output_path ), image )