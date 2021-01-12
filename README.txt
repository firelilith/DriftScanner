This is a work in progress (read: just barely usable) tool for analysing the photometry of star trails and
digitally improving the seeing of it.

main.py provides the App class that is the actual main window you want to be using to measure data.

dataanalyzer.py provides the class DataAnalyzer, the table window that lists all taken measurements and allows you
    to select and inspect them for further analysis. It also contains the MeasureWindow class, that displays different
    things depending on it's init parameter graph_type.

datasample.py provides the DataSample class, that represents an individual data sample with functions to get all the
    relevant measurements from it.