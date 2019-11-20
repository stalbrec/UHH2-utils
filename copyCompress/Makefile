CXXFLAGS := -O3 -g $(shell root-config --cflags)

LDFLAGS := $(shell root-config --ldflags)
LIBS := $(shell root-config --libs) -lTreePlayer

all: copyAndCompress countEvents

copyAndCompress: copyAndCompress.cc
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(LIBS) -o $@ $^

countEvents: countEvents.cc
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(LIBS) -o $@ $^

.PHONY: clean
clean:
	rm copyAndCompress countEvents
