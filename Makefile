doc:
	groff -mandoc -Thtml elogviewer.1 > html/index.html

upload-doc:
	rsync -avzP -e ssh html/ mathias_laurin@web.sourceforge.net:/home/project-web/elogviewer/htdocs/ 
	
