# delete me when done

class EventlogPlugin:
    """ log pytest events to a file. """
 
    def pytest_addoption(self, parser):
        parser.addoption("--eventlog", dest="eventlog",
            help="write all pytest events to the given file.")
 
    def pytest_configure(self, config):
        eventlog = config.getvalue('eventlog')
        if eventlog:
            self.eventlogfile = open(eventlog).open('w')
 
    def pytest_unconfigure(self, config):
        if hasattr(self, 'eventlogfile'):
            self.eventlogfile.close()
            del self.eventlogfile
 
    def pyevent(self, eventname, *args, **kwargs):
        if hasattr(self, 'eventlogfile'):
            print >>self.eventlogfile, eventname, args, kwargs
            self.eventlogfile.flush()
