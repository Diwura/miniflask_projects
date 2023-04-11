from PIL import Image

def processor(filename):
    file = './static/process/'+filename
    #an instance of the Image class from PIL is used to to open the file, convert it  
                                #and then save it with the same name
    img = Image.open(file)      
    grey = img.convert('L')
    grey.save(file)