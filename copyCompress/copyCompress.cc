#include <iostream>

#include "TFile.h"
#include "TTree.h"

using namespace std;


/**
 * Copy TTree from src to dest, with maximum compression applied.
 * NB is slow, and also requires you to be in the same version of UHH2 as ntuples produced,
 * to ensure class dictionaries are correct.
 */
void copyCompress(std::string src, std::string dest) { 
  TFile * fin = TFile::Open(src.c_str());
  if (fin->IsZombie() || fin == nullptr) {
    throw runtime_error("Couldn't open source " + src);
  }
  TTree * tree = (TTree*) fin->Get("AnalysisTree");
  if (tree == nullptr) {
    throw runtime_error("Couldn't get tree from " + src);
  }
  TFile * fout = TFile::Open(dest.c_str(), "RECREATE", "", 209); // set maximally compressed
  if (fout->IsZombie() || fout == nullptr){
    throw runtime_error("Couldn't open destination " + src);
  }
  TTree * newTree = tree->CloneTree(); // don't use "fast" to ensure compressed correctly
  newTree->Write();
  fout->Close();
  fin->Close();
}


int main(int argc, char** argv) {
  if (argc != 3) {
    throw runtime_error("Usage: ./copyCompress <source> <destination>");
  }
  copyCompress(argv[1], argv[2]);
  return 0;
}