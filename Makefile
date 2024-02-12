.PHONY: install uninstall

install:
	cp thingiverse-publisher /usr/local/bin/thingiverse-publisher

uninstall:
	rm -f /usr/local/bin/thingiverse-publisher
