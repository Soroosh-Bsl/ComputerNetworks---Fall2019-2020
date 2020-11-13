package com.company;

import java.io.Serializable;

class Payload implements Serializable {
    private String type;
    private String subType;
    private String subSubType;
    private String message;

    Payload(String type, String subType, String message) {
        this.type = type;
        this.subType = subType;
        this.message = message;
    }

    String getSubSubType() {
        return subSubType;
    }

    void setSubSubType(String subSubType) {
        this.subSubType = subSubType;
    }

    String getType() {
        return type;
    }

    String getSubType() {
        return subType;
    }

    String getMessage() {
        return message;
    }

}
