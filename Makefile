public/index.html: layouts/index.html
	hugo
clean:
	@rm -r public
install:
	rsync $(RSYNC_OPTIONS) -r public/* $(WEBSITE_REMOTE_USER)@$(WEBSITE_REMOTE_HOST):$(WEBSITE_REMOTE_PATH)/
