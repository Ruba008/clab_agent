import logging, sys

_configuration_done = False

def loggerConfiguration():
    
    global _configuration_done
    if _configuration_done:
        return
    
    LOG_FORMAT = (
        '[%(asctime)s] [%(levelname)-8s] '
        '[%(name)s:%(lineno)d] - %(message)s'
    )
    
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler("my_app.log")  
        ]
    )
    
    logging.getLogger(__name__).info("☑️ Logger configuration done.")
    _configuration_done = True