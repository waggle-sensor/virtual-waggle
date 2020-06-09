package main

import (
	"flag"
	"log"
	"net/http"
	"os"
)

var rootDir = flag.String("root", ".", "root directory for data")

func makeStreamHandler(name string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// we assume that http.ServeFile will add the headers
		// Accept-Ranges: bytes
		// Content-Type: *video mimetype*
		http.ServeFile(w, r, name)
	}
}

func main() {
	flag.Parse()

	http.HandleFunc("/bottom", makeStreamHandler("./bottom.mp4"))
	http.HandleFunc("/top", makeStreamHandler("./top.mp4"))

	log.Printf("serving data from %s", *rootDir)
	os.Chdir(*rootDir)
	log.Fatal(http.ListenAndServe(":5000", nil))
}
