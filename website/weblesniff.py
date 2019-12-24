#!/usr/bin/env python
'''
create png files for images
A. Rest
'''
import argparse
import glob
import os,re,sys,types,copy,random,time

import astropy.io.fits as fits
import numpy as np
import pylab
from   matplotlib.ticker import FormatStrFormatter,MultipleLocator
#import lc_ex

from tools import makepath4file,rmfile

def imagestring4web(imagename,width=None,height=None):
    #imstring = '<img src="%s"' % os.path.basename(imagename)
    imstring = '<img src="%s"' % imagename
    if height != None:
        if type(height) is types.IntType: height = str(height)
        imstring += '; height=%s' % height
    if width != None:
        if type(width) is types.IntType: width = str(width)
        imstring += '; width=%s' % width
    imstring +='>'
    return(imstring)

def addlink2string(s,link,target=None):
    line = '<a '
    if target != None:
        line += 'target="%s"' % target
    line += 'href="%s">%s</a>' % (link,s)
    return(line)

def addtag2string(s,tag,target=None):
    line = '<a name="%s"></a>%s' % (tag,s)
    return(line)

class htmltable:
    def __init__(self,Ncols,font=None,fontscale=None,fontsize=None,color=None,bgcolor=None,cellpadding=2,cellspacing=2,border=1,
                 width='100%',height=None,textalign='center',verticalalign='top',optionalarguments=''):
        self.Ncols = Ncols
        self.font  = font
        self.fontscale  = fontscale
        self.fontsize  = fontsize
        self.color      = color
        self.bgcolor    = bgcolor
        self.cellpadding = cellpadding
        self.cellspacing = cellspacing
        self.border      = border
        self.width       = width
        self.height      = height
        self.textalign   = textalign
        self.verticalalign=verticalalign
        self.optionalarguments  = optionalarguments
        self.tabletitle = None
        self.body = []

    def startrow(self,style = ''):
        self.body.append('<tr %s>' % style)
    def endrow(self):
        self.body.append('</tr>\n')

    def addcol(self,colval,link=None, verticalalign=None, textalign=None,
               colspan=None,rowspan=None,
               bold=None, italic=None, underline = None, 
               width=None, height=None, 
               color = None, bgcolor = None, font=None, fontscale=None, fontsize=None):
        if colval is None:
            colval = '-'  # placeholder!
            
        if link != None:
            colval = '<a href="%s">%s</a>' % (link,colval)

        pre   = ''
        after = ''
        #if textalign != None:
        #    pre   += '<%s>'  % (textalign)
        #    after  = '</%s>' % (textalign) + after
        if font != None:
            pre   += '<span style="font-family: %s;">' % (font)
            after  = '</span>' + after
        if fontsize != None:
            if type(fontsize) is types.StringType: fontsize = int(fontsize)
            pre   += '<font size=%d>' % (fontsize)
            after  = '</font>' + after
        if fontscale != None:
            pre   += '<font size="%s">' % (fontscale)
            after  = '</font>' + after
        if bold != None and bold != 0:
            pre   += '<b>'
            after  = '</b>'
        if  underline != None and underline != 0:
            pre   += '<u>'
            after  = '</u>'
        if italic != None and italic != 0:
            pre   += '<b>'
            after  = '</b>'
        if color != None:
            if type(color) is types.IntType: color = str(color)
            pre   += '<font color=%s>' % (color)
            after  = '</font>' + after
            
        line = '<td'
        if textalign != None:
            line += ' ALIGN="%s"' % textalign            
        if width != None:
            if type(width) is types.IntType: width = str(width)
            line += ' WIDTH="%s"' % width            
        if height != None:
            if type(height) is types.IntType: height = str(height)
            line += ' HEIGHT="%s"' % height            
        if verticalalign != None:
            line += ' VALIGN="%s"' % verticalalign            
        if bgcolor != None:
            if type(bgcolor) is types.IntType: bgcolor = str(bgcolor)
            line += ' BGCOLOR="%s"' % (bgcolor)
        if colspan != None:
            line += ' colspan="%d"' % (colspan)
        if rowspan != None:
            line += ' rowspan="%d"' % (rowspan)
        #if line != '<td':
        #    line += ' NOSAVE'
        line += '>'
        line += pre + colval + after + '</td>'
            
        self.body.append(line)

    def add_sorttablescript_before_header(self):
        return('<script type="text/javascript" src="sortable.js"></script>')

    def settabletitle(self,tabletitle,align='center',fontsize_pt=None,color='white',bgcolor='blue'):
        if tabletitle==None:
            self.tabletitle = None
        
        s = '<div '
        if align!=None: s+='align="%s"; ' % align
        s+= 'style="'
        if fontsize_pt!=None: s+='font-size: %dpt;' % fontsize_pt
        if color!=None: s+='color:%s;' % color
        if bgcolor!=None: s+='background-color:%s;' % bgcolor
        s+= '">'

        self.tabletitle = [s]
        self.tabletitle.append(tabletitle)
        self.tabletitle.append('</div>')
        return(0)

    def gettable(self, sortable=False):

        tableinitstring = '<table '
        # sortable columns?
        if sortable:
            tableinitstring += 'class="sortable" id="anyid" '
        # note: you also have to put the call 

        tableinitstring += 'style="'
        if self.textalign!=None:tableinitstring+='text-align: %s;' % (self.textalign)
        if self.width!=None:tableinitstring+='width: %s;' % (self.width)
        if self.font!=None:tableinitstring+='font-family: %s;' % (self.font)
        if self.fontscale!=None:tableinitstring+='font size: %s;>' % (self.fontscale)
        if self.fontsize!=None:
            tableinitstring+='font size: %d;>' % (int(self.fontsize))
        tableinitstring += '"'
        if self.color!=None:tableinitstring+='color="%s" ' % (self.color)
        if self.bgcolor!=None:tableinitstring+='bgcolor="%s" ' % (self.bgcolor)
        
        tableinitstring += ' COLS=%d BORDER=%d CELLSPACING=%d CELLPADDING=%d %s ' % (self.Ncols,self.border,self.cellspacing,self.cellpadding,self.optionalarguments)
        tableinitstring += '>'


        t=[]
        # Is there a title?
        if self.tabletitle != None: t.extend(self.tabletitle)

        # initialize the table
        t.append(tableinitstring)

        if sortable:
            t.append('<script type="text/javascript" src="sortable.js"></script>')

        # add the body
        t.extend(self.body)

        # close the table
        t.append('</table>')
        t.append('')

        return(t)

        
class webpageclass:
    def __init__(self):
        self.lines=[]
    def substituteplaceholder(self, pattern2find, newlines,count=0):
        import types
        patternobject = re.compile(pattern2find)
        print(newlines)
        if type(newlines) is types.StringType:
            s = newlines
        elif type(newlines) is types.ListType:
            s = '\n'.join(newlines)
        else:
            raise RuntimeError,'Error: unknown type, dont know how to deal with ',newlines
        for i in range(len(self.lines)):
            self.lines[i] = patternobject.sub(s,self.lines[i])
        
    def loaddefaultpage(self,filename):
        if not os.path.isfile(filename):
            raise RuntimeError,'ERROR: could not find file '+filename
        self.lines = open(filename).readlines()

    def savepage(self,filename):
        # Makesure the directory exists
        dir = os.path.dirname(filename)
        if not os.path.exists(dir):  os.makedirs(dir)  # This is a recursive mkdir
        rmfile(filename)
        f = open(filename,'w')
        f.writelines(self.lines)
        f.close()


class weblesniffclass:
    def __init__(self):
        self.verbose=0
        self.debug=0
        self.webdir = None
        self.figsuffix = 'jpg'
        self.usebinnedflag = False

        self.webdir = None
        self.imagelist_htmltemplate = None

        self.imagetableheaderfontscale = "+1"
        self.imagetablefontscale = None

        self.font = 'sans-serif'
        self.bgcolor1imtable = '#%02x%02x%02x' % (255,255,220)
        self.bgcolor4tableheader = '#E0FFFF'
        self.NotAvailable = '-'

    def define_options(self, parser=None, usage=None, conflict_handler='resolve'):
        if parser is None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler=conflict_handler)
        parser.add_argument("webdir", help=("web directory"))
        parser.add_argument("date", help=("date of observation"))
        parser.add_argument("imagelist_htmltemplate", help=("template for the html page"))
        parser.add_argument('--figsuffix', default='jpg',
                            help=('Define the type of figure you want to save (default=%(default)s)'))
        parser.add_argument('--rootwebaddress', default=None,
                            help=('Define the root of the webaddress (default=%(default)s)'))
        parser.add_argument('--usebinned', help="Use the gis from the binned diffims",
                            action="store_true", default=False)
        parser.add_argument('--verbose', '-v', action='count')
        parser.add_argument('-d', '--debug', help="debug", action='count')

        return(parser)

    def getfiglist(self):
#        if self.usebinnedflag:
#            figpattern = '*.bin.%s' % self.figsuffix
#        else:
        figpattern = '20[0-9][0-9]*[0-9][0-9][0-9][0-9]_texas.%s' % self.figsuffix
#        figlc = '20[0-9][0-9]*[0-9][0-9][0-9][0-9]_lc.%s' % self.figsuffix
        
        self.figlist = {}
        self.figlist['target']=[]
        self.figlist['images']=[]
#        self.figlist['lc']=[]
        self.figlist['date']=[]
        imgdir = '%s/%s' % (self.webdir,'plots/'+self.date)
        print('imgdir=',imgdir, figpattern)
        flist = glob.glob('%s/%s' % (imgdir,figpattern))
        print('flist=',flist)
        if len(flist)>0:
            i=0
            for fname in flist:
                fnameshort = os.path.relpath(fname,start=self.webdir)
                print(fnameshort)
                print(re.search('\d+\D+\d+_', fnameshort).group())
                objname = re.search('\d+\D+\d+_', fnameshort).group()[:-5]
                objdate = re.search('\d+\D+\d+_', fnameshort).group()[-5:-1]
#                    m = re.search('\w+\d+\.',fnameshort)#'\w+\d+\_+\d+\.',fnameshort)
#                    print(m)
                print(objname, objdate)
                imname = objname+objdate+'_texas.png'
                self.figlist['target'].append(objname)
                self.figlist['images'].append([imname, re.sub('texas', 'lc',imname)])

 #               self.figlist['lc']=.append([fnameshort, objname+objdate+'_lc.png'])
                self.figlist['date'].append(objdate)
                i=i+1

    def getwebaddress(self,field,tag=None):
        if self.rootwebaddress == None: return None
        webaddress = '%s/%s/index.html#%s' % (self.rootwebaddress,field,tag)
        return(webaddress)
    
    def makewebpage(self,p='1000'):
        colors4tmpl = [self.bgcolor1imtable,'lightcyan']
        # first, get fig files...
        self.getfiglist()
        
#        print(self.date, self.webdir)
        self.webfilename = '%s/%s.html' % (self.webdir, self.date)
        webpage = webpageclass()
        webpage.loaddefaultpage(self.imagelist_htmltemplate)

        webpage.substituteplaceholder('PLACEHOLDER_TITLE_PLACEHOLDER', os.path.basename(self.webdir))
        webpage.substituteplaceholder('PLACEHOLDER_BACKTOMAINLINK_PLACEHOLDER', addlink2string('BACK','..'))
        

        infotable = htmltable(2,border=1,cellspacing=0,cellpadding=2,width='1000px',textalign='center',verticalalign='center',fontscale=self.imagetablefontscale,font=self.font,bgcolor=self.bgcolor1imtable)
        field = os.path.basename(self.webdir)
        imcounter = 0
        print(self.figlist['images'])
        if len(self.figlist['images'])>0:
            for target in self.figlist['target']:
                infotable.startrow()
                infotable.addcol('', bgcolor = 'red')
                tag = target
                s = addtag2string(target,tag)
#                print(self.figlist['date'])
                webaddress = self.getwebaddress(target,tag=tag)
                if webaddress != None: s+='<br><font size=5>'+webaddress+'</font>'
                #s+='<br><font size=5>'
                #s+=addlink2string('zs9cmd','%d/zs9cmd.txt' % ccd)
                #s+='   '+addlink2string('zs9cmd.diff','%d/zs9cmd.diff.txt' % ccd)
                #s+='   '+addlink2string('zs9cmd.diff.bin','%d/zs9cmd.diff.bin.txt' % ccd)
                #s+='   '+addlink2string('tarcmd','%d/tarcmd.txt' % ccd)
                #s+='</font>'
                infotable.addcol(s, color = 'white', bgcolor = 'red', fontsize=20)
                infotable.endrow()
                tmplcounter=0
                print('figlist=', self.figlist)

                img = self.figlist['images'][imcounter]
                #print('img=',img)
                infotable.startrow()
                infotable.addcol('', bgcolor=colors4tmpl[imcounter % 2])
                infotable.addcol(self.figlist['date'][imcounter], fontsize=10)
#                infotable.addcol(details, fontsize=5)


                infotable.endrow()
#                    print('tmplID',tmplID,self.figlist[ccd][tmplID])
#                for im1 in img:

                infotable.startrow()
                        
                tag = 'im%d' % (imcounter+1)
                s_next = addlink2string('next','#im%d' % (imcounter+2))
                if imcounter>0:
                    s_prev = addlink2string('prev','#im%d' % (imcounter))
                else:
                    s_prev = ''
                s_back = addlink2string('back','..')
                    #s = addtag2string('%s<br>prev' % (s_next),tag)
                s = '%s<br>%s<br>%s' % (s_next,s_prev,s_back)
                infotable.addcol(s, verticalalign='top',fontsize=10,bgcolor=colors4tmpl[imcounter % 2])
#                        if self.usebinnedflag:
#                            im2 = re.sub('bin\.%s' % self.figsuffix,self.figsuffix,im1)
#                        else:
#                            im2 = re.sub(self.figsuffix,'bin\.%s' % self.figsuffix,im1)
#                        print(im1,im2)
			
#                        im2 = re.sub('texas', 'lc',im1)
#                        print('im1&2 = ', im1, im2)
                        
                s = addlink2string(imagestring4web(img[0],width=None,height=500),img[0])
                s = addtag2string(s,tag)
                infotable.addcol(s)  
                s = addlink2string(imagestring4web(img[1],width=None,height=500),img[1])
                s = addtag2string(s,tag)
                infotable.addcol(s)  
                infotable.endrow()
                tmplcounter+=1
                imcounter+=1

                    
        webpage.substituteplaceholder('PLACEHOLDER_IMAGETABLE_PLACEHOLDER', infotable.gettable())
        webpage.substituteplaceholder('PLACEHOLDER_LASTUPDATE_PLACEHOLDER', '%s' % time.asctime())
       
        print '### Saving ',self.webfilename
        webpage.savepage('./plots/%s/%s' % (self.date,self.webfilename))

        del webpage

            
if __name__ == '__main__':

#    info =lc_ex.main(351.8348167,41.5839778, '2019uag', '0000') 
#    print(info)
    
    weblesniff = weblesniffclass()
    parser = weblesniff.define_options()
    args = parser.parse_args()


    weblesniff.webdir = args.webdir
    weblesniff.date = str(args.date)
    weblesniff.imagelist_htmltemplate = args.imagelist_htmltemplate
#    print(weblesniff.date, args.date)

    if args.verbose>=1:
        print("webdir:    {}".format(weblesniff.webdir))
        
    if args.figsuffix != None:
        weblesniff.figsuffix = args.figsuffix
    weblesniff.usebinnedflag = args.usebinned
    weblesniff.rootwebaddress = args.rootwebaddress
        
    # set verbose, debug, and onlyshow level
    weblesniff.verbose = args.verbose
    weblesniff.debug = args.debug

    weblesniff.makewebpage()
    
    print("weblesniff SUCCESS")