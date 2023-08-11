PY?=python3
SED=$(shell which gsed 2>/dev/null || which sed)
PELICAN?=pelican
PELICANOPTS=

BASEDIR=$(CURDIR)
INPUTDIR=$(BASEDIR)/content
OUTPUTDIR=$(BASEDIR)/output
CONFFILE?=$(BASEDIR)/pelicanconf.py
PUBLISHCONF=$(BASEDIR)/publishconf.py

SSH_HOST=webhost
SSH_PORT=22
SSH_TARGET_DIR=~/glennklockwood.com/

PORT=8000

DEBUG ?= 0
ifeq ($(DEBUG), 1)
	PELICANOPTS += -D
endif

RELATIVE ?= 0
ifeq ($(RELATIVE), 1)
	PELICANOPTS += --relative-urls
endif

help:
	@echo 'Makefile for a pelican Web site                                           '
	@echo '                                                                          '
	@echo 'Usage:                                                                    '
	@echo '   make html                           (re)generate the web site          '
	@echo '   make clean                          remove the generated files         '
	@echo '   make regenerate                     regenerate files upon modification '
	@echo '   make publish                        generate using production settings '
	@echo '   make serve [PORT=8000]              serve site at http://localhost:8000'
	@echo '   make serve-global [SERVER=0.0.0.0]  serve (as root) to $(SERVER):80    '
	@echo '   make devserver [PORT=8000]          serve and regenerate together      '
	@echo '   make ssh_upload                     upload the web site via SSH        '
	@echo '   make rsync_upload                   upload the web site via rsync+ssh  '
	@echo '                                                                          '
	@echo 'Set the DEBUG variable to 1 to enable debugging, e.g. make DEBUG=1 html   '
	@echo 'Set the RELATIVE variable to 1 to enable relative urls                    '
	@echo '                                                                          '

NOTEBOOKS = content/pages/data-intensive/analysis/perceptron.ipynb \
            content/pages/data-intensive/analysis/multilayer-perceptron.ipynb

BENCHMARK_FILES = content/data/benchmarks/arm_processors.yaml \
                  content/data/benchmarks/mips_processors.yaml \
                  content/data/benchmarks/power_processors.yaml \
                  content/data/benchmarks/x86_processors.yaml \
                  content/data/benchmarks/ia64_processors.yaml \
                  content/data/benchmarks/parisc_processors.yaml \
                  content/data/benchmarks/sparc_processors.yaml
#
#  Super hacky piece to convert very specific Jupyter notebooks into very
#  specific Markdown pages.  This is an imperfect process and usually requires
#  hand-hacking, but it's better than nothing right now.
#
content/pages/data-intensive/analysis/perceptron.md: notebooks/perceptron.ipynb
	(jupyter nbconvert --to markdown "$<" \
	&& mv -v notebooks/perceptron.md "$@" \
	&& mkdir -p content/static/data-intensive/analysis \
	&& mv -v notebooks/perceptron_files/* content/static/data-intensive/analysis/ \
	&& $(SED) -i 's#perceptron_files/##g' "$@" \
	&& $(SED) -i '0,/^# \(.*\)/{s//---\ntitle: \1\norder: 10\nmathjax: True\n---\n\n/}' "$@" \
	&& $(SED) -i 's/\([^\]\)_{/\1\\_{/g' "$@" \
	&& rmdir notebooks/perceptron_files) || rm "$@"

content/pages/data-intensive/analysis/multilayer-perceptron.md: notebooks/multilayer-perceptron.ipynb
	(jupyter nbconvert --to markdown "$<" \
	&& mv -v notebooks/multilayer-perceptron.md "$@" \
	&& mkdir -p content/static/data-intensive/analysis \
	&& (test ! -d notebooks/multilayer-perceptron_files || mv -v notebooks/multilayer-perceptron_files/* content/static/data-intensive/analysis/) \
	&& $(SED) -i 's#multilayer-perceptron_files/##g' "$@" \
	&& $(SED) -i '0,/^# \(.*\)/{s//---\ntitle: \1\norder: 15\nmathjax: True\n---\n\n/}' "$@" \
	&& $(SED) -i 's/\([^\]\)_{/\1\\_{/g' "$@" \
	&& (test ! -d notebooks/multilayer-perceptron_files || rmdir notebooks/multilayer-perceptron_files)) || rm "$@"

content/static/benchmarks/benchmark-results.json: $(BENCHMARK_FILES)
	$(PY) -mlimeleadlib.benchmarks $^ -o "$@"

html: $(NOTEBOOKS:ipynb=md) content/static/benchmarks/benchmark-results.json
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

clean:
	[ ! -d $(OUTPUTDIR) ] || rm -rf $(OUTPUTDIR)

regenerate:
	$(PELICAN) -r $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

serve:
ifdef PORT
	$(PELICAN) -l $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS) -p $(PORT)
else
	$(PELICAN) -l $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)
endif

serve-global:
ifdef SERVER
	$(PELICAN) -l $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS) -p $(PORT) -b $(SERVER)
else
	$(PELICAN) -l $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS) -p $(PORT) -b 0.0.0.0
endif


devserver:
ifdef PORT
	$(PELICAN) -lr $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS) -p $(PORT)
else
	$(PELICAN) -lr $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)
endif

publish:
	$(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(PUBLISHCONF) $(PELICANOPTS)

ssh_upload: publish
	scp -P $(SSH_PORT) -r $(OUTPUTDIR)/* $(SSH_HOST):$(SSH_TARGET_DIR)

rsync_upload: publish
	rsync -e "ssh -p $(SSH_PORT)" -P -rvzc --cvs-exclude --exclude .well-known --delete $(OUTPUTDIR)/ $(SSH_HOST):$(SSH_TARGET_DIR)


.PHONY: html help clean regenerate serve serve-global devserver publish ssh_upload rsync_upload
