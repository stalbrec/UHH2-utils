#include <iostream>

#include "TFile.h"
#include "TTree.h"
#include "TTreeReader.h"

using namespace std;


int countTreeEventsFast(TFile * f) {
  TTree * tree = (TTree*) f->Get("AnalysisTree");
  if (tree == nullptr) {
    throw runtime_error("Couldn't get tree from TFile");
  }
  return tree->GetEntriesFast();
}

int countTreeEventsSlow(TFile * f) {
  // Could we just use TTree->GetEntries() here instead? Or GetEntries("")?
  // (since the former just returns a class variable)
  TTreeReader myReader("AnalysisTree", f);
  int nEvents = 0;
  while (myReader.Next()) {
    nEvents++;
  }
  return nEvents;
}

/**
 * Count number of events in TTree.
 * mode == "1" for fast, "0" for actually iterating through tree
 * Latter ensures you read each entry in the tree.
 */
int countEvents(std::string src, std::string mode) {
  TFile * fin = TFile::Open(src.c_str());
  if (fin->IsZombie() || fin == nullptr) {
    throw runtime_error("Couldn't open source " + src);
  }
  int result = 0;
  if (mode == "1") {
    result = countTreeEventsFast(fin);
  } else {
    result = countTreeEventsSlow(fin);
  }
  fin->Close();
  return result;
}

int main(int argc, char** argv) {
  if (argc != 3) {
    throw runtime_error("Usage: ./countEvents <source> <1 for fast, 0 for tree iteration>");
  }
  int num = countEvents(argv[1], argv[2]);
  cout << num << endl;
  return 0;
}