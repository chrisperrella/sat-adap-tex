def blank_image( output_path, width, height ):
    import numpy, cv2
    image = numpy.zeros( ( width, height, 3 ) )
    cv2.imwrite( str( output_path ), image )

def random_hex_color():
    import random
    return '{:02x}{:02x}{:02x}'.format( random.randint( 0, 255 ), random.randint( 0, 255 ), random.randint( 0, 255 ) )