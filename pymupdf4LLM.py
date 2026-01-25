import pymupdf, pymupdf4llm

filename = "source_doc/Datacenter NVMe SSD Specification v2.0r21.pdf"
#filename = "source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"
#filename = "source_doc/NVM-Express-Base-Specification-Revision_2P3.pdf" 
doc = pymupdf.open(filename)  # use a Document for subsequent processing
tocs = doc.get_toc()  # use the table of contents for determining headers

def toc_gen():
    for toc in tocs:
        toc_level=toc[0]
        toc_title=toc[1]
        toc_page=toc[2]

        if toc_title.find("Bit")>0:
            print(f'toc_level={toc_level}, toc_title={toc_title}, toc_page={toc_page}')



if __name__ == "__main__":  
    toc_gen()  




