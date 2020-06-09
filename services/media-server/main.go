package main

import (
	"flag"
	"log"
	"net/http"
	"os"
)

func makeStreamHandler(name string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// we assume that http.ServeFile will add the headers
		// Accept-Ranges: bytes
		// Content-Type: *video mimetype*
		http.ServeFile(w, r, name)
	}
}

func main() {
	dataDir := flag.String("data", ".", "path to data directory")
	flag.Parse()

	http.HandleFunc("/live", makeStreamHandler("./bottom.mp4")) // keep ffserver endpoint
	http.HandleFunc("/bottom", makeStreamHandler("./bottom.mp4"))
	http.HandleFunc("/top", makeStreamHandler("./top.mp4"))

	log.Printf("serving data from %s", *dataDir)
	os.Chdir(*dataDir)
	log.Fatal(http.ListenAndServe(":8090", nil))
}
