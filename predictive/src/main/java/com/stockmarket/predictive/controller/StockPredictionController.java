package com.stockmarket.predictive.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

@RestController
@RequestMapping("/api/stocks")
public class StockPredictionController {

    @GetMapping("/predict")
    public ResponseEntity<?> predict(@RequestParam String symbol, @RequestParam(defaultValue = "5d") String period) {
        String prediction = callPythonService(symbol, period);
        return ResponseEntity.ok(prediction);
    }

    private String callPythonService(String symbol, String period) {
        try {
            URL url = new URL("http://localhost:5000/predict?symbol=" + symbol + "&period=" + period);
            HttpURLConnection con = (HttpURLConnection) url.openConnection();
            con.setRequestMethod("GET");

            BufferedReader in = new BufferedReader(
                    new InputStreamReader(con.getInputStream())
            );
            String inputLine;
            StringBuffer content = new StringBuffer();
            while ((inputLine = in.readLine()) != null) {
                content.append(inputLine);
            }
            in.close();
            return content.toString();
        } catch (Exception e) {
            return "Error: " + e.getMessage();
        }
    }
}
