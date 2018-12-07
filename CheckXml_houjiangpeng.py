#-*-coding=utf8-*-

import os,sys
import time,thread
from lxml import etree
import hashlib
from StringIO import StringIO
import re

def log_error(str):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    sys.stderr.write('[%s] [%d] [error] %s\n' % (time_str, thread.get_ident(), str))
    sys.stderr.flush()
def log_info(str):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    sys.stdout.write('[%s] [%d] [info] %s\n' % (time_str, thread.get_ident(), str))
    sys.stdout.flush()

def checkAttribute(baseNode,testNode,xpathStr=''):
    if baseNode is None:
        return
    for key in baseNode.keys():
        base_val = baseNode.get(key)
        test_nodes = testNode.xpath(xpathStr)
        if len(test_nodes) ==0 :
            log_error('[checkAttribute] the test xpage has no node %s/@%s ' % (xpathStr,key) )
        elif len(test_nodes)==1:
            cur_node=test_nodes[0]
            test_val = cur_node.get(key)
            if test_val is None:
                log_error('[checkAttribute] test xpage has no Attribute, xpath: %s/@%s base_val=%s' % (xpathStr,key,base_val) )
            elif base_val!= test_val:
                log_error('[checkAttribute] diff Attribute, xpath: %s/@%s,  test attr:%s,   base arrt:%s' % (xpathStr,key,test_val,base_val) )
        else:
            log_error('[checkAttribute] test xpage has same node %s/@%s ' % (xpathStr,key) )
    return 1
def checkText(baseNode,testNode,xpathStr=''):
    if baseNode is None or testNode is None:
        return
    baseText=baseNode.text
    if baseText is None:
        return
    hash_base=hashlib.md5(baseText).hexdigest()
    test_nodes = testNode.xpath(xpathStr)
    if len(test_nodes)==0:
        log_error('[checkText] the test xpage has no node %s' % ( xpathStr ) )
    elif len(test_nodes)==1:
        cur_node=test_nodes[0]
        testText=cur_node.text
        if testText is None:
            log_error('[checkText] test xpage has no Text, xpath:%s, test text is None' % xpathStr )
        else:
            hash_test=hashlib.md5(testText).hexdigest()
            #log_info('[checkText] hash_base=%s hash_test=%s ' % (hash_base, hash_test))
            if hash_test != hash_base:
                #log_error('[checkText] diff Text, xpath:%s\n|______base text: %s\n|______test text: %s\n' % (xpathStr,baseText, testText) )
                log_error('[checkText] diff Text, xpath:%s\n' % (xpathStr) )
    else:
        log_error('[checkText] the test xpage has same node %s ' % (xpathStr) )

def checkXml(baseRoot,testRoot,xpathStr=''):
    if testRoot is None:
        return
    if baseRoot is None:
        return
    xpath_str='%s/%s'%(xpathStr,baseRoot.tag)
    checkAttribute(baseRoot,testRoot,xpath_str)
    checkText(baseRoot,testRoot,xpath_str)
    #print xpath_str
    for filed in baseRoot:
        checkXml(filed, testRoot, xpath_str)
def strQ2B(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:
            inside_code = 32 
        elif (inside_code >= 65281 and inside_code <= 65374):
            inside_code -= 65248
        rstring += unichr(inside_code)
    return rstring
def uniformCharset(inputStr):
    output=strQ2B(inputStr)
    output=output.replace('encoding="UTF-16"','encoding="UTF-8"')
    output=output.decode('gb18030','ignore').encode('utf-8')
    #output=strQ2B(output)
    return output

def getLine(line):
    line_lst = line.split('\t')
    key = line_lst[0]
    val = '\t'.join(line_lst[1:])
    return key,val
def procOne(xmlTest,xmlBase,key):
    
    xmlTest=uniformCharset(xmlTest)
    xmlBase=uniformCharset(xmlBase)
    testRoot=None
    baseRoot=None
    try: 
        testRoot=etree.fromstring(xmlTest)
    except Exception,err:
        log_error('procOne etree test %s err : %s' % (key, err) )
        return False
    try:
        baseRoot=etree.fromstring(xmlBase)
    except Exception,err:
        log_error('procOne etree base %s err : %s' % (key, err) )
        return False
    
    log_info('[procOne] %s the old index is base'%key)
    checkXml(baseRoot, testRoot)
    
    log_info('[procOne] %s the new index is base'%key)
    checkXml(testRoot, baseRoot)

    return True
if __name__=='__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')

    if len(sys.argv)==3:
        basexml_file=sys.argv[1]
        testxml_file=sys.argv[2]
    else:
        basexml_file="/search/odin/task/new_index1/tool/one_base.txt"
        testxml_file="/search/odin/task/new_index1/tool/one_test.txt"
    
    log_error('[main] proc base xml: %s test xml %s , len(sys.argv)=%d' % (basexml_file,testxml_file,len(sys.argv)))
    
    basexml_dict={}
    with open(basexml_file,'r') as fd:
        for line in fd:
            key,val=getLine(line)
            val_lst=val.split('</xpage>')
            val=val_lst[0]+"</xpage>"
            basexml_dict[key]=val

    with open(testxml_file,'r') as fd:
        for line in fd:
            key,xml_test=getLine(line)
            if not basexml_dict.has_key(key):
                log_error('the test xml file %s has no xpage %s' % (testxml_file,key))
                continue
            xml_base=basexml_dict.get(key)
            procOne(xml_test,xml_base,key)
