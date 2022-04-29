def blank_image( output_path, width, height ):
    import numpy, cv2
    image = numpy.zeros( ( width, height, 3 ) )
    cv2.imwrite( str( output_path ), image )

def random_hex_color():
    import random
    return '{:02x}{:02x}{:02x}'.format( random.randint( 0, 255 ), random.randint( 0, 255 ), random.randint( 0, 255 ) )

def get_obj_materials( obj_path ):
    import pywavefront
    scene = pywavefront.Wavefront( str( obj_path ),  create_materials=True )
    scene.parse()
    materials = list()
    for name, material in scene.materials.items():
        materials.append( material.diffuse )
    return materials

def rgb_to_hex( rgb ):
    import matplotlib
    if len(rgb) > 3:
        return matplotlib.colors.to_hex(rgb)
    else:
        return matplotlib.colors.to_hex(rgb, keep_alpha=False)