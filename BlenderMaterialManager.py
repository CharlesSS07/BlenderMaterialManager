bl_info = {
    "name": "Blender-Material-Manager",
    "version": (0,0),
    "blender": (2,80,0),
    "author": "Charles S Strauss <charles.s.strauss@gmail.com>",
    "description": "Easy access online materials manager.",
    "category": "Material Settings"
}

import bpy
import os.path as paths
import os
import sys
#sys.path.append('/home/shelby/blender_2.8/addons/BlenderMaterialManager/BlenderMaterialManager')
#sys.path.append('/home/shelby/blender_2.8/addons/BlenderMaterialManager/BlenderMaterialManager/python-socketio')
#sys.path.append('/home/shelby/blender_2.8/addons/BlenderMaterialManager/BlenderMaterialManager/python-engineio')
#sys.path.append('/home/shelby/.local/lib/python3.6/site-packages/python_socketio-4.0.3.dev0-py3.6.egg')
#sys.path.append('/usr/local/anaconda3/lib/python3.6/site-packages')
import requests
import subprocess
import socketio
import eventlet
import webbrowser
from gevent import pywsgi

class BlenderMaterialManager(bpy.types.Operator):
    """Downloads and installs materials for easy access."""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "materials.bmm"        # unique identifier for buttons and menu items to reference.
    bl_label = "Blender Material Manager"         # display name in the interface.
    bl_description = "Onlie Asset Downloader and Installer."  # enable undo for the operator.

    #img_quality = bpy.props.IntProperty('Quality', 'Larger images take up more ram. Select 1K, 2K, 4K, 8K, 16K.', default=4, soft_min=0, soft_max=16, get=)
    
    def on_mat_selection(self, sid, pic_id):
        print('material selected:', pic_id)
    
    def execute(self, context):        # execute() is called by blender when running the operator.
        print('BlenderMaterialManager executed')
        return {'FINISHED'}            # this lets blender know the operator finished successfully.

class MaterialManagerPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Blender Material Manager --"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        wm = context.window_manager
        #row = self.layout.row()
        #row.prop(wm.rb_filter, "rb_filter_enum", expand=True)
        row = self.layout.row()
        row.operator("bmm.texturehaven", text='TextureHaven.com')
        row = self.layout.row()



class WebParser():
    
    class Resources():

        SUMMARY_FILE = '/home/shelby/Resources/textures/.summary.txt'
        DIR = '/home/shelby/Resources/textures/'
        CACHE_DIR = '/home/shelby/Resources/textures/.cache/'

        def get_count():
            with open(Resources.SUMMARY_FILE, 'r') as f:
                a = len(f.readlines())
            return a

        def get_name(img_quality, map_type, file_type):
            '''Names all images according to same convention.'''
            num = '%06d' % Resources.get_count() 
            return num+'_%s_%s.%s'%(img_quality, map_type, file_type)

        def write(url, quality, filetype, filename, source, is_zip, map_type):
            with open(Resources.SUMMARY_FILE, 'a+') as f:
                f.write('\t'.join([self.filename, *self.fingerprint.values(), self.url])+'\n')
    
    def __init__(self):
        
        self.save_loc = paths.abspath(paths.join(self.get_website_dir(), self.get_source_name(), 'index.html'))
        self.script_loc = 'file://'+paths.abspath(paths.join(self.get_website_dir(), self.get_source_name(), 'script.js'))
    
    def get_website(self):
        '''Gets html for website. Injects js scripts necessary for server.'''
        w = requests.get(self.get_full_url()).text.replace('</head>', '<script src="file:///home/shelby/blender_2.8/addons/BlenderMaterialManager/BlenderMaterialManager/socket.io-client/dist/socket.io.js"></script></head>').replace('</body>', '<script src="%s"></script></body>'%(self.script_loc))
        return self.preprocess_website(w)
    
    def get_source_name(self):
        return None
    
    def get_website_dir(self):
        return 'websites'
    
    def get_url(self):
        return None
    
    def get_full_url(self):
        return None
    
    def preprocess_website(self, w):
        '''What to do to the website to make it useable. Returns html.'''
        return w
    
    def get_img_urls(self, pic_id, img_quality, file_type):
        '''Finds all urls that need to be downloaded for this material. Including color, bump, normal, roughness...'''
        return ['http://images7.memedroid.com/images/UPLOADED628/587fe55c29eb7.jpeg', 'https://pics.me.me/60-of-the-time-it-works-every-time-60-of-15242762.png', 'https://pbs.twimg.com/media/DvFsnoDXQAAaCaW.jpg', 'https://www.memecreator.org/static/images/memes/4982344.jpg']
    
    def get_map_type(self, path):
        '''Highly universal function for deciding what kind of map this file is. Is is a color map? Is it a roughness map? Is it a bump map?'''
        maps = {
            'color': ['color', 'diffuse', 'diff', 'albedo'],
            'rough': ['roughness', 'rough', 'rgh'],
            'metal': ['metal', 'metallic', 'met'],
            'height':['height', 'disp', 'displacement'],
            'normal':['normal', 'nor', 'nrm', 'bump'],
            'spec':  ['spec', 'specular', 'specularity'],
            'ao':    ['ao', 'ambientocclusion', 'ambient_occlusion'],
            'mask':  ['mask', 'alpha']
        }
        f = path.split('/')[-1].lower() # get file, instead of path, make it lower case, because we don't care about case
        for i, k in enumerate(maps):
            for v in maps[k]:
                if v in f:
                    return k
        raise Exception('Function get_map_type could not discriminate the type of map:%s. Implement your own to resolve this error.'%(f))
    
    def download_and_organize(self, pic_id, img_quality, file_type):
        '''Downloads the images, returned by get_img_urls, unzips zip if file is zip. Names according to order of image in dir.'''
        files = {}
        for url in self.get_img_urls(pic_id, img_quality, file_type):
            o = paths.join(Resources.CACHE_DIR, 'bmm_%s_cache.zip'%(self.get_source_name()))
            subprocess.check_output(['curl', url, '-o', o])
            if o[-3:]=='zip':
                uz = o[:-4]
                subprocess.check_output(['unzip', o, '-d', uz])
                for f in os.listdir(uz):
                    map_type = self.get_map_type(f)
                    n = paths.join(Resources.DIR, Resources.get_name(img_quality, map_type, file_type))
                    subprocess.run(['mv', paths.join(uz, f), n])
                    files[map_type] = n
                    Resources.write(url, img_quality, file_type, n, self.get_source_name(), True, map_type)
                # remove zip file...
            else:
                map_type = self.get_map_type(o)
                n = paths.join(Resources.DIR, Resources.get_name(img_quality, map_type, file_type))
                subprocess.run(['mv', o,  n])
                Resources.write(url, img_quality, file_type, n, self.get_source_name(), False, map_type)
                files[map_type] = n
        return files

class MaterialServer():
    
    def __init__(self):
        self.sio = socketio.Server()
    
    def start(self):
        self.sio = socketio.Server()
        index_loc = self.get_index_loc()
        
        self.app = socketio.WSGIApp(self.sio, static_files={
            '/': index_loc,
            'socket.io.js': self.get_socketio_loc(),
            'script.js': self.get_script_loc()
        })
        
        with open(index_loc, 'w') as f:
            f.write(self.get_website())
        webbrowser.open(index_loc, new=1, autoraise=True)

        self.sio.on('connect', self.connect)
        self.sio.on('disconnect', self.disconnect)
        self.sio.on('submitresource', self.on_material_select)
        eventlet.wsgi.server(eventlet.listen(('127.0.0.1', 6006)), self.app)
    
    def get_socketio_loc(self):
        return './socket.io-client/dist/socket.io.js'
    
    def get_script_loc(self):
        return '/tmp/script.js'
    
    def get_index_loc(self):
        return '/tmp/index.html'
    
    def get_website(self):
        return 'Override get_website from MaterialServer to prevent this error.'
    
    def connect(self, sid, data):
        print("I'm connected!")

    def disconnect(self, sid):
        print("I'm disconnected!")

    def on_material_select(self, sid, pic_id):
        print('Image Selected:', pic_id)
        self.wp.download_and_organize(pic_id, self.img_quality, self.file_type)
        # load into blender...
        print('textures downloaded! ready to load into blender')

class TextureHavenButton(bpy.types.Operator, WebParser, MaterialServer):
    bl_idname='bmm.texturehaven'
    bl_label = 'Material'
    
    def __init__(self):
        print('TextureHavenButton init')
        super().__init__()
    
    def connect(self, sid, data):
        print("Socket connected!")

    def disconnect(self, sid):
        print("Socket disconnected!")

    def get_script_loc(self):
        return './websites/TextureHaven.com/script.js'

    def get_index_loc(self):
        return 'addons/BlenderMaterialManager/BlenderMaterialManager/websites/TextureHaven.com/index.html'

    def on_material_select(self, sid, pic_id):
        print('Image Selected:', pic_id)
        self.download_and_organize(pic_id, self.img_quality, self.file_type)
        # load into blender...
        print('textures downloaded! ready to load into blender')

    def get_source_name(self):
        return 'TextureHaven.com'

    def get_url(self):
        return 'https://texturehaven.com/'
    
    def get_full_url(self):
        return 'https://texturehaven.com/textures/'

    def preprocess_website(self, w): # overidden for webparser
        return w.replace('\\', '').replace('"', "'").replace("'./", "'"+self.get_url()).replace("'/", "'"+self.get_url())

    def get_img_urls(self, pic_id, img_quality, file_type): # overidden for webparser
        url = 'https://texturehaven.com/files/textures/zip/%s/%s/%s_%s_%s.zip'
        return [url%(img_quality, pic_id, pic_id, img_quality, file_type)]

    def execute(self, context):
        print('Material button pressed')
        self.start()
        print('Material button depressed')
        return {'FINISHED'}

def register():
    from bpy.utils import register_class
    register_class(BlenderMaterialManager)
    register_class(MaterialManagerPanel)
    register_class(TextureHavenButton)

def unregister():
    bpy.utils.unregister_class(BlenderMaterialManager)
    bpy.utils.unregister_class(MaterialManagerPanel)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
