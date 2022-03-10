def blank_image( output_path, width, height ):
    import numpy, cv2
    image = numpy.zeros( ( width, height, 3 ) )
    cv2.imwrite( str( output_path ), image )