
bl_info = {
    "name": "TextureHavenMaterialManager",
    "version": (0,0,1),
    "blender": (2,80,0),
    "author": "Charles S Strauss <charles.s.strauss@gmail.com>",
    "description": "A test addon",
    "category": "Materials"
}

import bpy

import webbrowser
import socket
import requests
import os
import subprocess

class WebParser():
    
    class Resources():

        SUMMARY_FILE = os.path.expanduser('~/Resources/textures/.summary.txt')
        DIR = os.path.expanduser('~/Resources/textures/')
        CACHE_DIR = os.path.expanduser('~/Resources/textures/.cache/')

        def get_count():
            with open(WebParser.Resources.SUMMARY_FILE, 'r') as f:
                a = len(f.readlines())
            return a

        def get_name(img_quality, map_type, file_type):
            '''Names all images according to same convention.'''
            num = '%06d' % WebParser.Resources.get_count() 
            return num+'_%s_%s.%s'%(img_quality, map_type, file_type)
        
        def is_downloaded(url):
            '''Returns files locations if true, returns False if resource is not downloaded.'''
            with open(WebParser.Resources.SUMMARY_FILE, 'r') as f:
                downloaded = False
                lines = {}
                for l in  f.readlines(): # split lines leaves the \n on each line
                    fp = l.split('\t')
                    if fp[1]==url:
                        downloaded = True
                        map_type = fp[5][:-1] # get last element, which should have a \n on it becuse of how split lines works
                        lines[map_type] = fp[0]
                if downloaded:
                    return lines
                return False
        
        def write(url, quality, filetype, filename, source, is_zip, map_type):
            with open(WebParser.Resources.SUMMARY_FILE, 'a+') as f:
                f.write('\t'.join([filename, url, filetype, source, str(is_zip), map_type])+'\n')
    
    def __init__(self):
        self.request_session = requests.Session()

        pass
    
    def get_website(self, local_url):
        '''Gets html for website. Injects js scripts necessary for server.'''
        base_url = self.get_full_url()
        if base_url[-1]=='/' and local_url[0]=='/':
            base_url=base_url[:-1]
        url = base_url+local_url
        print(url)
        w = self.request_session.get(url).text
        #w = w.replace('</body>', '<script type="text/javascript></script>%s</body>'%(self.get_return_script()))
        w = self.preprocess_website(w) # mabey just foward from socket, instead of doing tricky buisness.
        w = w.replace('</body>', '\n<script>%s</script>\n</body>'%(self.get_script()))
        #w = w.replace('</title>', '</title><base href="%s">'%self.get_url())
        #w = w.replace('"/', self.get_url())
        #w = w.replace("'/", self.get_url())
        #w = w.replace("'./", self.get_url())
        #print(w)
        return w
    
    def get_source_name(self):
        raise NotImplementedError
    
    def get_url(self):
        raise NotImplementedError
    
    def get_full_url(self):
        raise NotImplementedError
    
    #def get_return_script(self, port):
    #    '''Returns a js function, called send_pic_id, for using in js script. This js function will send the pic_id to the specified port. Its only arguements are pic_id.'''
    #    return 'function send_pic_id(pic_id){var xmlHttp = null;xmlHttp = new XMLHttpRequest();xmlHttp.open("GET","http://localhost:%s/?pic_id="+JSON.stringify(pic_id), true);xmlHttp.send(null);}'%port
    
    def get_script(self):
        '''Returns script to be run in browser, to make website interact correctly.'''
        return 'alert("Please Implement get_script(), to supress this message.");'
    
    def preprocess_website(self, w):
        '''What to do to the website to make it useable. Returns html.'''
        raise NotImplementedError
    
    def get_img_urls(self, pic_id, img_quality, file_type):
        '''Finds all urls that need to be downloaded for this material. Including color, bump, normal, roughness...'''
        return ['http://images7.memedroid.com/images/UPLOADED628/587fe55c29eb7.jpeg', 'https://pics.me.me/60-of-the-time-it-works-every-time-60-of-15242762.png', 'https://pbs.twimg.com/media/DvFsnoDXQAAaCaW.jpg', 'https://www.memecreator.org/static/images/memes/4982344.jpg']
    
    def get_map_type(self, path, pic_id):
        '''Highly universal function for deciding what kind of map this file is. Is is a color map? Is it a roughness map? Is it a bump map?'''
        maps = {
            'color': ['color', 'diffuse', 'diff', 'albedo'],
            'rough': ['roughness', 'rough', 'rgh'],
            'metal': ['metal', 'metallic', 'met'],
            'height':['height', 'disp', 'displacement', 'bump'],
            'normal':['normal', 'nor', 'nrm'],
            'spec':  ['spec', 'specular', 'specularity'],
            'ao':    ['ao', 'ambientocclusion', 'ambient_occlusion'],
            'mask':  ['mask', 'alpha']
        }
        f = path.replace(pic_id, '') # to get rid of useless or confusing words, like in the pic_id "rough_block_wall_..." rough is accidentally interpreted.
        f = f.split('/')[-1].lower() # get file, instead of path, make it lower case, because we don't care about case
        for k in maps:
            for v in maps[k]:
                #print('Here', k, v)
                if v in f:
                    #print('Key:', k)
                    return k
        raise Exception('Function get_map_type could not discriminate the type of map:%s. Implement your own to resolve this error.'%(f))
    
    def download_and_organize(self, pic_id, img_quality, file_type):
        '''Downloads the images, returned by get_img_urls, unzips zip if file is zip. Names according to order of image in dir.'''
        files = {}
        for url in self.get_img_urls(pic_id, img_quality, file_type):
            downloaded = WebParser.Resources.is_downloaded(url)
            if downloaded is not False:
                files = {**downloaded, **files}
            else:
                o = os.path.join(WebParser.Resources.CACHE_DIR, 'bmm_%s_cache.zip'%(self.get_source_name()))
                subprocess.check_output(['curl', url, '-o', o])
                if o[-3:]=='zip':
                    uz = o[:-4]
                    subprocess.check_output(['unzip', o, '-d', uz])
                    for f in os.listdir(uz):
                        map_type = self.get_map_type(f, pic_id)
                        n = os.path.join(WebParser.Resources.DIR, WebParser.Resources.get_name(img_quality, map_type, file_type))
                        subprocess.run(['mv', '--force', os.path.join(uz, f), n])
                        files[map_type] = n
                        WebParser.Resources.write(url, img_quality, file_type, n, self.get_source_name(), True, map_type)
                    # remove zip file...
                else:
                    map_type = self.get_map_type(o, pic_id)
                    n = os.path.join(WebParser.Resources.DIR, WebParser.Resources.get_name(img_quality, map_type, file_type))
                    subprocess.run(['mv', '--force', o,  n])
                    WebParser.Resources.write(url, img_quality, file_type, n, self.get_source_name(), False, map_type)
                    files[map_type] = n
        return files

class MaterialServer(WebParser):
    
    def start(self, port):
        #print('starting server')
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        c.bind(('localhost', port))
        webbrowser.open('http://localhost:%s'%port, new=1, autoraise=True)
        c.listen(1)
        running = True
        while running:
            csock, caddr = c.accept() 
            cfile = csock.makefile('rw', 100) 
            line = cfile.readline().strip().split(' ')
            print(line)

            #cfile.write('HTTP/1.0 200 OK\n\n')
            #valid = True
            #if len(line[1])!=3:
            #    valid = False
            #if valid:
            #    request = line[1].split('=')
            #    if request[0]=='/?pic_id':
            #        pic_id = request[1]
            #        cfile.write('<html><head><title>GetPicID</title></head>')
            #        cfile.write('<body><h1>Success! pic_id:%s</h1>'%pic_id)
            #        cfile.write('</body></html>')
            #        self.on_material_select(pic_id)
            #        running = False
            #    else:
            #        cfile.write(self.get_website(line[1]))
            #else:
            #    cfile.write(self.get_website(line[1]))

            if line[1] == '/':
                page=  self.get_website(line[1])
                #print(page)
                #print('page start:', page, '--page end')
                cfile.write('HTTP/1.0 200 OK\n\n')
                cfile.write(page)
            else:
                if '?' in line[1]:
                    #print('found ?')
                    if '=' in line[1].split('?')[1]:
                        #print('found =')
                        if 'pic_id' in line[1]:
                            pic_id = line[1].split('=')[1]
                            #print('found pic_id: %s'%pic_id)
                            cfile.write('HTTP/1.0 200 OK\n\n')
                            cfile.write('<html><head><title>GetPicID</title></head>')
                            cfile.write('<body><h1>Success! pic_id:%s</h1>'%pic_id)
                            cfile.write('</body></html>')
                            self.on_material_select(pic_id)
                            running = False
            cfile.close() 
            csock.close() 
        
    
    def on_material_select(self, pic_id):
        raise NotImplementedError

class TextureHavenProperties(bpy.types.PropertyGroup):

    img_quality = bpy.props.EnumProperty(name='Quality', description='select number of pixels', items=[('1k', '1K', 'short download'),('2k', '2K', ''),('4k', '4K', ''),('8k', '8K', 'very long download')])
    img_type = bpy.props.EnumProperty(name='Type', description='file type to download', items=[('png', 'PNG', 'higher quality, longer download'),('jpg', 'JPG', 'lower quality, short download')])

class MATERIAL_OT_startbutton(bpy.types.Operator, MaterialServer):
    bl_idname = 'material.thstartbutton'
    bl_label = 'Start Button'

    def on_material_select(self, pic_id):
        #print('Image Selected:', pic_id)
        files = self.download_and_organize(pic_id, bpy.context.scene.thmm.img_quality, bpy.context.scene.thmm.img_type)
        # load into blender...
        # create shader, name it <pic_id>
        maps = {
            'color': ['Base Color', 0],# translation of may types to inputs on principled shader
            'rough': ['Roughness', -250],
            'metal': ['Metallic', -500],
            'spec':  ['Specular', -1000],
            'ao':    ['Base Color', -100],# for now
            'mask':  ['Alpha', -1500]
        }
        mat = bpy.data.materials.new(pic_id) # create a new material for now. mabey check to see if this material is already created in future to avoid overriding current materials.
        # start populating tree with required nodes
        mat.use_nodes = True
        links = mat.node_tree.links
        for n in mat.node_tree.nodes:
            mat.node_tree.nodes.remove(n)
        principled_node = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        output_node = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location.x = 1250/2
        links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
        displacement_node = mat.node_tree.nodes.new(type='ShaderNodeDisplacement')
        displacement_node.location.x = 750/2
        displacement_node.location.y = -250/2
        links.new(displacement_node.outputs['Displacement'], output_node.inputs['Displacement'])
        normal_map_node = mat.node_tree.nodes.new(type='ShaderNodeNormalMap')
        normal_map_node.location.x = -900/2
        normal_map_node.location.y = -1000/2
        bump_node = mat.node_tree.nodes.new(type='ShaderNodeBump')
        bump_node.location.x = -400/2
        bump_node.location.y = -900/2
        links.new(normal_map_node.outputs['Normal'], bump_node.inputs['Normal'])
        links.new(bump_node.outputs['Normal'], principled_node.inputs['Normal'])
        tex_coords_node = mat.node_tree.nodes.new(type='ShaderNodeTexCoord')
        tex_coords_node.location.x = -2700/2
        mapping_node = mat.node_tree.nodes.new(type='ShaderNodeMapping')
        mapping_node.location.x = -2200/2
        links.new(tex_coords_node.outputs['UV'], mapping_node.inputs['Vector'])
        for k in files:
            f = files[k]
            # load images into blender
            fname = os.path.basename(f)
            img_data = bpy.ops.image.open(filepath=f, directory=os.path.dirname(f), files=[{"name":fname, "name":fname}], show_multiview=False)
            img_data = bpy.data.images[fname] # get the image that was just loaded
            # create nodes
            img_node = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
            # set color transforms to Non-Color for most image types

            # set correct color space settings.
            img_data.colorspace_settings.name = "Non-Color"
            if k=='color':
                img_data.colorspace_settings.name = "sRGB"

            # set image node to use the the correct image
            img_node.image = img_data

            # minimize the image node, because this shouldn't need much more editing by the user.
            img_node.hide = True

            # link image node to mapping node
            links.new(mapping_node.outputs['Vector'], img_node.inputs['Vector'])

            # link image node to correct socket, based off of map type (color, normal, roughness...) also, set positions in node editor
            img_node.location.x = -1500/2
            if k not in {'height', 'normal', 'ao'}:
                img_node.location.y = maps[k][1]
                links.new(img_node.outputs['Color'], principled_node.inputs[maps[k][0]])
            elif k=='height':
                img_node.location.y = -900/2
                links.new(img_node.outputs['Color'], displacement_node.inputs['Height'])
                links.new(img_node.outputs['Color'], bump_node.inputs['Height'])
            elif k=='normal':
                img_node.location.y = 300/2
                links.new(img_node.outputs['Color'], normal_map_node.inputs['Color'])
            elif k=='ao':
                img_node.location.y = 400/2
                pass # don't seem to have a use for the ao texture. Could this be extra?
            else:
                raise TypeError('May type, %s, was not found.'%k)


        print('textures downloaded! ready to load into blender')

    def get_source_name(self):
        return 'TextureHaven.com'
    
    def get_script(self):
        return '''
            function set_broadcast_on_click(){
                var imgs = document.getElementsByClassName('grid-item');
                //alert("broadcast on click set");
                for (var i =0;i<imgs.length;i++){
                    imgs[i].onclick = function(){
                        //alert("image selected!");
                        var pic_id = this.childNodes[1].childNodes[0].childNodes[0].childNodes[0].innerHTML;
                        var xhr = new XMLHttpRequest();
                        xhr.onload = function(){
                            //alert (xhr.responseText);
                            var w = window.innerWidth*0.7;
                            var h = window.innerHeight*0.7;
                            window.open('https://www.patreon.com/TextureHaven/overview', 'DONATE!!', "height="+w+",width="+h);
                            //realized I switched h and w, but like the resulting sidepanel.
                        } // success case
                        xhr.onerror = function(){ alert (xhr.responseText); } // failure case
                        xhr.open ('GET', 'http://localhost:6007/?pic_id='+pic_id, true);
                        xhr.send (pic_id);
                    }
                }
            }
            //alert('script ran');
            window.onload = set_broadcast_on_click;
            '''
    
    def get_url(self):
        return 'https://texturehaven.com/'
    
    def get_full_url(self):
        return 'https://texturehaven.com/textures/'

    def preprocess_website(self, w):
        return w.replace('\\', '').replace('"', "'").replace("'./", "'"+self.get_url()).replace("'/", "'"+self.get_url())

    def get_img_urls(self, pic_id, img_quality, file_type): # overidden for webparser
        files = ['https://texturehaven.com/files/textures/zip/%s/%s/%s_%s_%s.zip'%(img_quality, pic_id, pic_id, img_quality, file_type)]
        #print('url:', files)
        return files

    def execute(self, context):
        scene = context.scene
        bmm = scene.thmm
        #print('Material button pressed')
        port = 6007
        #print('starting server thread')
        self.start(port)
        #print('server thread started')
        #print('Material button depressed')
        return {'FINISHED'}

class MATERIAL_PT_manager(bpy.types.Panel):
    bl_idname = 'material.manager'
    bl_label='TextureHaven.com Material Manager'
    bl_context = 'material'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'Materials'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bmm = scene.thmm
        layout.prop(bmm, 'img_quality')
        layout.prop(bmm, 'img_type')
        layout.operator('material.thstartbutton', text='TextureHaven.com')
        layout.separator()
    

classes = [TextureHavenProperties, MATERIAL_OT_startbutton, MATERIAL_PT_manager]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.thmm = bpy.props.PointerProperty(type=TextureHavenProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    del bpy.types.Scene.thmm

if __name__=='__main__':
    register()
