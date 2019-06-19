
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
        
        pass
    
    def get_website(self):
        '''Gets html for website. Injects js scripts necessary for server.'''
        w = requests.get(self.get_full_url()).text
        #w = w.replace('</body>', '<script type="text/javascript></script>%s</body>'%(self.get_return_script()))
        w = w.replace('</body>', '<script type="text/javascript>%s</script></body>'%(self.get_script()))
        w = self.preprocess_website(w)
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
    
    @staticmethod
    def get_map_type(path):
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

class MaterialServer(WebParser):
    
    def start(self, port):
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        c.bind(('localhost', port))
        c.listen(1)
        running = True
        while running:
            csock, caddr = c.accept() 
            cfile = csock.makefile('rw', 100) 
            line = cfile.readline().strip().split(' ')
            print(line)
            if line[1] == '/':
                page=  self.get_website()
                #print('page start:', page, '--page end')
                cfile.write('HTTP/1.0 200 OK\n\n')
                cfile.write(page)
            else:
                if '?' in line[1]:
                    print('found ?')
                    if '=' in line[1].split('?')[1]:
                        print('found =')
                        if 'pic_id' in line[1]:
                            pic_id = line[1].split('=')[1]
                            print('found pic_id: %s'%pic_id)
                            cfile.write('HTTP/1.0 200 OK\n\n')
                            cfile.write('<html><head><title>GetPicID</title></head>')
                            cfile.write('<body><h1>Success! pic_id:%s</h1>'%pic_id)
                            cfile.write('</body></html>')
                            self.on_material_select(pic_id)
                            running = False
            cfile.close() 
            csock.close() 
        
    
    def on_material_select(self, pic_id):
        print('Image Selected:', pic_id)
        self.download_and_organize(pic_id, self.img_quality, self.file_type)
        # load into blender...
        print('textures downloaded! ready to load into blender')