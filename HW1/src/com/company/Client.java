package com.company;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.*;
import java.util.Scanner;


public class Client {
    private Socket clientSocket;
    private String serverIP;
    private int serverPort;
    private ObjectOutputStream outStream;

    private ObjectOutputStream getOutStream() {
        return outStream;
    }

    private ObjectInputStream getInputStream() {
        return inputStream;
    }

    private ObjectInputStream inputStream;

    private Client(String serverIP, int serverPort) {
        this.serverIP = serverIP;
        this.serverPort = serverPort;
        try {
            this.clientSocket = new Socket(this.serverIP, this.serverPort);
        }
        catch (IOException exception){
            System.out.println("Could not connect to server, possibly unknown host");
        }
        try {
            this.outStream = new ObjectOutputStream(this.clientSocket.getOutputStream());
            this.inputStream = new ObjectInputStream(this.clientSocket.getInputStream());
        }
        catch (IOException | NullPointerException exception){
            System.out.println("Streams could not be established");
        }
    }

    public static void main(String[] args) {
        Client client = new Client("localhost", 5000);
        while(true){
            Payload payloadIn = null;
              try {
                  payloadIn = (Payload) client.getInputStream().readObject();
            } catch (IOException | ClassNotFoundException exception){
                  System.out.println("Disconnected from server.");
                  try {
                      client.getInputStream().close();
                      client.getOutStream().close();
                      client.clientSocket.close();
                      break;
                  } catch (IOException e) {
                      e.printStackTrace();
                  }
            }
            Payload payloadOut = null;
            if (payloadIn.getType().equals("login")){
                Scanner scanner = new Scanner(System.in);
                if (payloadIn.getSubType().equals("username")){
                    System.out.println(payloadIn.getMessage());
                    payloadOut = new Payload("login", "username", scanner.next());
                }
                else if (payloadIn.getSubType().equals("password")){
                    System.out.println(payloadIn.getMessage());
                    payloadOut = new Payload("login", "password", scanner.next());
                }
                else if (payloadIn.getSubType().equals("success")){
                    System.out.println(payloadIn.getMessage());
                    String option = scanner.next();
                    if (option.equals("cmd")){
                        payloadOut = new Payload("cmd", "enter", "");
                    }
                    else if (option.equals("message_mode")){
                        payloadOut = new Payload("message mode", "enter", "");
                    }
                    else if (option.equals("log_out")){
                        payloadOut = new Payload("log out", "", "");
                    }
                }
            }
            else if (payloadIn.getType().equals("cmd")){
                if (payloadIn.getSubType().equals("enter")){
                    System.out.println(payloadIn.getMessage());
                    Scanner scanner = new Scanner(System.in);
                    String command = scanner.nextLine();
                    if (command.equals("BACK")){
                        payloadOut = new Payload("cmd", "finish", "");
                    }
                    else{
                        payloadOut = new Payload("cmd", "command", command);
                    }
                }
            }
            else if (payloadIn.getType().equals("message mode")){
                if (payloadIn.getSubType().equals("enter")){
                    System.out.println(payloadIn.getMessage());
                    Scanner scanner = new Scanner(System.in);
                    String option = scanner.next();
                    if (option.equals("send")){
                        payloadOut = new Payload("message mode", "send", "");
                        payloadOut.setSubSubType("enter");
                    }
                    else if (option.equals("receive")){
                        payloadOut = new Payload("message mode", "receive", "");
                        payloadOut.setSubSubType("enter");
                    }
                    else if (option.equals("unread")){
                        payloadOut = new Payload("message mode", "unread", "");
                        payloadOut.setSubSubType("enter");
                    }
                    else if (option.equals("BACK")){
                        payloadOut = new Payload("message mode", "finish", "");
                    }
                }
                else if (payloadIn.getSubType().equals("send")){
                    if (payloadIn.getSubSubType().equals("username")){
                        System.out.println(payloadIn.getMessage());
                        Scanner scanner = new Scanner(System.in);
                        String username = scanner.next();
                        if (username.equals("BACK")){
                            payloadOut = new Payload("message mode", "send", "\\BACK\\");
                            payloadOut.setSubSubType("username");
                        }
                        else{
                            payloadOut = new Payload("message mode", "send", username);
                            payloadOut.setSubSubType("username");
                        }
                    }
                    else if (payloadIn.getSubSubType().equals("message")){
                        System.out.println(payloadIn.getMessage());
                        String text;
                        Scanner scanner = new Scanner(System.in);
                        text = scanner.nextLine();
                        if (text.equals("BACK")){
                            payloadOut = new Payload("message mode", "send", "\\BACK\\");
                            payloadOut.setSubSubType("message");
                        }
                        else {
                            payloadOut = new Payload("message mode", "send", text);
                            payloadOut.setSubSubType("message");
                        }

                    }
                }
                else if (payloadIn.getSubType().equals("receive")){
                    if (payloadIn.getSubSubType().equals("done")) {
                        System.out.println(payloadIn.getMessage());
                        payloadOut = new Payload("message mode", "receive", "");
                        payloadOut.setSubSubType("done");
                    }
                }
                else if (payloadIn.getSubType().equals("unread")){
                    if (payloadIn.getSubSubType().equals("done")) {
                        System.out.println(payloadIn.getMessage());
                        payloadOut = new Payload("message mode", "unread", "");
                        payloadOut.setSubSubType("done");
                    }
                }

            }
            else if (payloadIn.getType().equals("log out")){
                payloadOut = new Payload("log out", "", "");
            }
            try {
                client.getOutStream().writeObject(payloadOut);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
