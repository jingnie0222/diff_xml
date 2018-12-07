#!/usr/bin/python
#-*-coding=utf8-*-
import os,sys
import time,thread
from lxml import etree
import hashlib
from StringIO import StringIO
import re
from urllib import unquote

def log_error(str):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    sys.stderr.write('[%s] [%d] [error] %s\n' % (time_str, thread.get_ident(), str))
    sys.stderr.flush()
def log_info(str):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    sys.stdout.write('[%s] [%d] [info] %s\n' % (time_str, thread.get_ident(), str))
    sys.stdout.flush()

def checkAttribute(baseNode,testNode,root,xpathStr=''):
    if baseNode is None:
        log_error('[checkAttribute] the base xml has no node %s' % xpathStr)
        return
    if testNode is None:
        log_error('[checkAttribute] the test xml has no node %s' % xpathStr)
        return
    base_nodes = baseNode.xpath(xpathStr)
    test_nodes = testNode.xpath(xpathStr)
    for key in baseNode.keys():
        if len(test_nodes) ==0 :
            log_error('[checkAttribute] the test xml has no Attribute %s/@%s ' % (xpathStr,key) )
        else:
            if len(base_nodes) != len(test_nodes):
                log_error('[checkAttribute] nodes number of base xml and text xml are not equal, xpath:%s ' % xpathStr )
                log_error('[checkAttribute] base node:%s' % etree.tostring(baseNode))
            else:
                #log_error('####### checkAttribute ########')
                for b_node, t_node in zip(base_nodes,test_nodes):
                    base_val = b_node.get(key)
                    test_val = t_node.get(key)
                    if base_val is None and test_val is None:
                        continue
                    elif base_val is None and test_val is not None:
                        log_error('[checkAttribute] base xml Attribute value is null, xpath: %s/@%s' % (xpathStr,key))
                        return
                    elif base_val is not None and test_val is None:
                        log_error('[checkAttribute] test xml Attribute value is null, xpath: %s/@%s' % (xpathStr,key))
                        return 

                    if base_val != test_val:
                        log_error('[checkAttribute] diff Attribute, xpath: %s/@%s,  test attr:%s,   base arrt:%s' % (xpathStr,key,test_val,base_val) )
    return 1

def checkText(baseNode,testNode,xpathStr=''):
    if baseNode is None:
        log_error('[checkText] baseNode is null, xpath:%s' % xpathStr)
        return
    if testNode is None:
        log_error('[checkText] testNode is null, xpath:%s' % xpathStr)
        return
    
    base_nodes = baseNode.xpath(xpathStr)
    test_nodes = testNode.xpath(xpathStr)
    
    if len(test_nodes)==0:
        log_error('[checkText] the test xml has no node %s' % ( xpathStr ) )
    else:
        if len(base_nodes) != len(test_nodes):
            log_error('[checkText] nodes number of base xml and text xml are not equal, xpath:%s ' % xpathStr )
        else:
            for b_node, t_node in zip(base_nodes,test_nodes):
                baseText = b_node.text
                testText = t_node.text
                if baseText is None and testText is None:
                    continue
                elif baseText is None and testText is not None:
                    log_error('[checkText] base node text is null, xpath:%s' % xpathStr )
                    return
                elif baseText is not None and testText is None:
                    log_error('[checkText] test node text is null, xpath:%s' % xpathStr )
                    return

                hash_base = hashlib.md5(baseText).hexdigest()
                hash_test = hashlib.md5(testText).hexdigest()
                if hash_test != hash_base:
                    log_error('[checkText] diff Text, xpath:%s\n|______base text: *%s*\n|______test text: *%s\n' % (xpathStr,baseText, testText) )

xpath_lst = []

def checkXml(baseRoot,testRoot,root,xpathStr=''):
    if testRoot is None:
        log_error('[checkXml] the test node is null, the xpath:%s' % xpathStr)
        return
    if baseRoot is None:
        log_error('[checkXml] the base node is null, the xpath:%s' % xpathStr)
        return

    xpath_str='%s/%s'%(xpathStr,baseRoot.tag)
    if xpath_str in xpath_lst:
        return
    xpath_lst.append(xpath_str)
    checkAttribute(baseRoot,testRoot,root,xpath_str)
    checkText(baseRoot,testRoot,xpath_str)
    for filed in baseRoot:
        checkXml(filed, testRoot, root, xpath_str)

def procOne(xmlTest,xmlBase,key):

    xmlTest=uniformCharset(xmlTest)
    xmlBase=uniformCharset(xmlBase)
    print '################################################',xmlBase
    testRoot=None
    baseRoot=None
    xmlp = etree.XMLParser(encoding="utf-8")

    try:
        testRoot=etree.fromstring(xmlTest, parser=xmlp)
    except Exception,err:
        log_error('procOne etree test %s err : %s' % (key, err) )
        return False
    try:
        baseRoot=etree.fromstring(xmlBase, parser=xmlp)
    except Exception,err:
        log_error('procOne etree base %s err : %s' % (key, err) )
        return False

    log_info('[procOne] %s the base xml  is baseline'%key)
    checkXml(baseRoot, testRoot, root=testRoot)

    log_info('[procOne] %s the test xml is baseline'%key)
    xpath_lst[:] = []
    checkXml(testRoot, baseRoot,root=testRoot)

    return True

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
    #output=output.replace('encoding="UTF-16"','encoding="UTF-8"')
    output=output.decode('gb2312','ignore').encode('utf8')
    return output

def getLine(line):
    line_lst = line.split('\t',1)
    key = line_lst[0]
    val = line_lst[1]
    return key,val
 


if __name__=='__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
 
    if len(sys.argv)==3:
        basexml_file=sys.argv[1]
        testxml_file=sys.argv[2]

    log_error('[main] proc base xml: %s test xml %s , len(sys.argv)=%d' % (basexml_file,testxml_file,len(sys.argv)))

    basexml_dict={}
    with open(basexml_file,'r') as fd:
        for line in fd:
            key,val=getLine(line)
            basexml_dict[key]=val

    with open(testxml_file,'r') as fd:
        for line in fd:
            key,xml_test=getLine(line)
            if not basexml_dict.has_key(key):
                log_error('the base xml file %s has no xml %s' % (basexml_file,key))
                continue
            xml_base=basexml_dict.get(key)
            procOne(xml_test,xml_base,key)

