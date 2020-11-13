package com.company;
import java.io.*;
import java.net.*;
import java.util.ArrayList;


class Message{
    private boolean read;
    private String text;
    private String senderUsername;

    Message(Boolean read, String text, String senderUsername) {
        this.read = read;
        this.text = text;
        this.senderUsername = senderUsername;
    }

    boolean getRead() {
        return read;
    }

    void setRead(boolean read) {
        this.read = read;
    }

    String getText() {
        return text;
    }

    String getSenderUsername() {
        return senderUsername;
    }

}

public class Server {
    private ServerSocket serverSocket;
    private ArrayList<String> usernames, passwords;
    private ArrayList<ArrayList> messages;

    private Server(int serverPort) {
        try{
            this.serverSocket = new ServerSocket(serverPort);
        } catch (IOException e){
            System.out.println("Server socket creation failed!");
        }
        this.usernames = new ArrayList<>();
        this.passwords = new ArrayList<>();
        this.messages = new ArrayList<>();
    }

    public static void main(String[] args) throws IOException{
        Server server = new Server(5000);
        while(true) {
            Socket socket = server.serverSocket.accept();
            final ObjectOutputStream outStream = new ObjectOutputStream(socket.getOutputStream());
            final ObjectInputStream inputStream = new ObjectInputStream(socket.getInputStream());
            new Thread(() -> {
                boolean askedUsername = false;
                boolean loggedIn = false;
                boolean askedPassword = false;
                Payload payloadOut = null, payloadIn = null;
                String username = null;
                String password;
                String recv_username = null;
               while(true){
                   if (!loggedIn){
                       if (!askedUsername){
                           payloadOut = new Payload("login", "username", "Please enter your username:");
                           askedUsername = true;
                       }
                       else {
                           if (!askedPassword){
                               try {
                                   payloadIn = (Payload) inputStream.readObject();
                               } catch (IOException e) {
                                   try {
                                       inputStream.close();
                                       socket.close();
                                       break;
                                   } catch (IOException ex) {
                                       ex.printStackTrace();
                                   }
                               } catch (ClassNotFoundException e) {
                                   e.printStackTrace();
                               }
                               if (payloadIn.getType().equals("login") && payloadIn.getSubType().equals("username")){
                                   username = payloadIn.getMessage();
                                   payloadOut = new Payload("login", "password", "Please enter your password:");
                                   askedPassword = true;
                               }
                           }
                           else{
                               try {
                                   payloadIn = (Payload) inputStream.readObject();
                               } catch (IOException | ClassNotFoundException e) {
                                   e.printStackTrace();
                               }
                               if (payloadIn.getType().equals("login") && payloadIn.getSubType().equals("password")){
                                   password = payloadIn.getMessage();
                                   if (!server.usernames.contains(username)){
                                       server.usernames.add(username);
                                       server.passwords.add(password);
                                       server.messages.add(new ArrayList<Message>());
                                       payloadOut = new Payload("login", "success", "Registered successfully!\nEnter one of options:\ncmd\nmessage_mode\nlog_out");
                                       loggedIn = true;
                                   }
                                   else if (server.passwords.get(server.usernames.indexOf(username)).equals(password)){
                                       payloadOut = new Payload("login", "success", "Logged in successfully!\nEnter one of options:\ncmd\nmessage_mode\nlog_out");
                                       loggedIn = true;
                                   }
                                   else {
                                       try {
                                           inputStream.close();
                                           socket.close();
                                           break;
                                       } catch (IOException e) {
                                           e.printStackTrace();
                                       }

                                   }
                               }
                           }
                       }
                   }
                   else{
                       try {
                           payloadIn = (Payload) inputStream.readObject();
                       } catch (IOException | NullPointerException e) {
                           try {
                               inputStream.close();
                               outStream.close();
                               socket.close();
                               break;
                           } catch (IOException ex) {
                               ex.printStackTrace();
                           }
                       } catch (ClassNotFoundException e) {
                           e.printStackTrace();
                       }
                       if (payloadIn.getType().equals("cmd")){
                            if (payloadIn.getSubType().equals("enter")){
                                payloadOut = new Payload("cmd", "enter", "Enter your command:");
                            }
                            else if (payloadIn.getSubType().equals("command")){
                                String results = "Results: \n";
                                ProcessBuilder builder = new ProcessBuilder(
                                        "cmd.exe", "/c", "cd \"D:\\University\" && "+payloadIn.getMessage());
                                builder.redirectErrorStream(true);
                                Process p = null;
                                try {
                                    p = builder.start();
                                } catch (IOException e) {
                                    e.printStackTrace();
                                }
                                BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
                                String line;
                                while (true) {
                                    line = null;
                                    try {
                                        line = r.readLine();
                                    } catch (IOException e) {
                                        e.printStackTrace();
                                    }
                                    if (line == null) { break; }
                                    results = results.concat(line+"\n");
                                }
                                payloadOut = new Payload("cmd", "enter", results + "\nEnter your new command:");
                            }
                            else if (payloadIn.getSubType().equals("finish")){
                                payloadOut = new Payload("login", "success", "Exited from cmd successfully!\nEnter one of options:\ncmd\nmessage_mode\nlog_out");
                            }
                        }
                        else if (payloadIn.getType().equals("message mode")){
                            if (payloadIn.getSubType().equals("enter")){
                                payloadOut = new Payload("message mode", "enter", "Entered message mode successfully.\nEnter one of options:\nsend\nreceive\nunread");
                            }
                            else if (payloadIn.getSubType().equals("send")){
                                if (payloadIn.getSubSubType().equals("enter")){
                                    payloadOut = new Payload("message mode", "send", "Enter receiver's username:");
                                    payloadOut.setSubSubType("username");
                                }
                                else if (payloadIn.getSubSubType().equals("username")){
                                    recv_username = payloadIn.getMessage();
                                    if (recv_username.equals("\\BACK\\")){
                                        payloadOut = new Payload("message mode", "enter", "Exited from send successfully!\nEnter one of options:\nsend\nreceive\nunread");
                                    }
                                    else if (server.usernames.contains(recv_username)){
                                        payloadOut = new Payload("message mode", "send", "Enter your message:");
                                        payloadOut.setSubSubType("message");
                                    }
                                    else{
                                        payloadOut = new Payload("message mode", "send", "Username not found!. Enter receiver's username:");
                                        payloadOut.setSubSubType("username");
                                    }
                                }
                                else if (payloadIn.getSubSubType().equals("message")){
                                    String text = payloadIn.getMessage();
                                    if (text.equals("\\BACK\\")){
                                        payloadOut = new Payload("message mode", "enter", "Exited from send successfully!\nEnter one of options:\nsend\nreceive\nunread");
                                    }
                                    else{
                                        Message message = new Message(false, text, username);
                                        server.messages.get(server.usernames.indexOf(recv_username)).add(message);
//                                        payloadOut = new Payload("message mode", "enter", "Message sent successfully.\nEnter one of options:\nsend\nreceive\nunread");
                                        payloadOut = new Payload("message mode", "send", "Message sent successfully. Enter your new message.\nEnter receiver's username:");
                                        payloadOut.setSubSubType("username");
                                        recv_username = null;
                                    }
                                }
                            }
                            else if (payloadIn.getSubType().equals("receive")){
                                if (payloadIn.getSubSubType().equals("done")){
                                    payloadOut = new Payload("message mode", "enter", "Back to message mode successfully.\nEnter one of options:\nsend\nreceive\nunread");
                                }
                                else if (payloadIn.getSubSubType().equals("enter")){
                                    String messages = "#####\nMessages:\n";
                                    if (server.messages.get(server.usernames.indexOf(username)).size() > 0){
                                        for (int i = 0; i < server.messages.get(server.usernames.indexOf(username)).size(); i++){
                                            messages = messages.concat("From: " + ((Message)server.messages.get(server.usernames.indexOf(username)).get(i)).getSenderUsername()+"\n");
                                            messages = messages.concat("Body: " + ((Message)server.messages.get(server.usernames.indexOf(username)).get(i)).getText()+"\n");
                                            ((Message)server.messages.get(server.usernames.indexOf(username)).get(i)).setRead(true);
                                            payloadOut = new Payload("message mode", "receive", messages);
                                            payloadOut.setSubSubType("done");
                                        }
                                    }
                                    else{
                                        payloadOut = new Payload("message mode", "receive", messages);
                                        payloadOut.setSubSubType("done");
                                    }
                                }
                            }
                            else if (payloadIn.getSubType().equals("unread")){
                                if (payloadIn.getSubSubType().equals("done")){
                                    payloadOut = new Payload("message mode", "enter", "Back to message mode successfully.\nEnter one of options:\nsend\nreceive\nunread");
                                }
                                else if (payloadIn.getSubSubType().equals("enter")){
                                    String messages = "#####\nMessages:\n";
                                    if (server.messages.get(server.usernames.indexOf(username)).size() > 0){
                                        for (int i = 0; i < server.messages.get(server.usernames.indexOf(username)).size(); i++){
                                            if (!((Message)server.messages.get(server.usernames.indexOf(username)).get(i)).getRead()) {
                                                messages = messages.concat("From: " + ((Message)server.messages.get(server.usernames.indexOf(username)).get(i)).getSenderUsername()+"\n");
                                                messages = messages.concat("Body: " + ((Message)server.messages.get(server.usernames.indexOf(username)).get(i)).getText()+"\n");
                                                ((Message)server.messages.get(server.usernames.indexOf(username)).get(i)).setRead(true);
                                            }
                                            payloadOut = new Payload("message mode", "unread", messages);
                                            payloadOut.setSubSubType("done");
                                        }
                                    }
                                    else{
                                        payloadOut = new Payload("message mode", "unread", messages);
                                        payloadOut.setSubSubType("done");
                                    }
                                }
                            }
                            else if (payloadIn.getSubType().equals("finish")){
                                payloadOut = new Payload("login", "success", "Exited from message mode successfully!\nEnter one of options:\ncmd\nmessage_mode\nlog_out");
                            }
                        }
                        else if (payloadIn.getType().equals("log out")){
                           try {
                               inputStream.close();
                               outStream.close();
                               socket.close();
                               break;
                           } catch (IOException e) {
                               e.printStackTrace();
                           }

                        }
                   }

                   try {
                       outStream.writeObject(payloadOut);
                   } catch (IOException e) {
                       try {
                           if (socket.isClosed()){
                               break;
                           }
                           outStream.close();
                           inputStream.close();
                           socket.close();
                       } catch (IOException ex) {
                           ex.printStackTrace();
                       }
                   }
               }

            }).start();
            System.out.println("One Client Added");
        }
    }
}
