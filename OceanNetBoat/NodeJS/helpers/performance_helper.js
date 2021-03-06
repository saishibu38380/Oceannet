/**
 * Created by nkn on 2/25/2015.
 */
"use strict";
var logger = require('./logger_helper').logger;
var models = require('../models');
var db = require('../db/db_connection_pool');
var error = require('../db/error');
var serverSocketHelper = require('./server-socket-helper');

var PerformanceHelper = {
    limit:50,
    sendFrequency:10*60*1000,
    findById:function(id){
        return models.performance.findById(id);
    },
    findAllPendingForRetry:function(limit,offset){
        return models.performance.findAll({where:{transferDate:{$eq:null}},order:[['timestamp','ASC']],offset: offset, limit: limit});
    },
    sendPendingRecords:function (offset,helper) {
        if(!serverSocketHelper.isConnected){
            return;
        }
        helper.findAllPendingForRetry(helper.limit,offset).then( (pendingPerformanceValues) =>{
            if(pendingPerformanceValues.length > 0){
                logger.info("Number of pending records for retry %d",pendingPerformanceValues.length);
                var serverSocketHelper = require('./server-socket-helper');
                serverSocketHelper.sendPerformanceBulkData(pendingPerformanceValues);
                if(pendingPerformanceValues.length < helper.limit){
                    helper.retryPendingRecords(0,this.sendFrequency);
                }else{
                    offset += pendingPerformanceValues.length;
                    helper.retryPendingRecords(offset);
                }
            }else{
                helper.retryPendingRecords(0,this.sendFrequency);
            }
        });
    },
    retryPendingRecords:function (offset=0,timeout=3000) {
        // var envConfig = require('./config_helper').envConfig;
        // logger.info("Retrying pending records with Offset %s",offset);
        var helper = this;
        setTimeout(helper.sendPendingRecords,timeout,0,helper);
    },
    bulkUpdate:function (ids) {
        db.pool.getConnection(function(err, myCon) {
            if (err) {
                logger.error("Error while acquiring connection:" + err);
                return;
            }
            if (!myCon) {
                logger.error("Error while acquiring connection:");
                return;
            }
            var updateQuery = "update performance ";
            updateQuery += "SET transferDate = NOW() "
            updateQuery += " Where id in (";
            updateQuery += ids.join(",");
            updateQuery += " )";
            // logger.info('updateQuery:'+updateQuery);
            myCon.query(updateQuery
                , function(err, results) {
                    error.handleConnectionError(err,myCon);
                    logger.info('Successfully updated data');
                    myCon.release(function(err) {
                        if(err)logger.error("Error while closing connection:"+err);
                    });
                });
        })
    },
    cleanup:function(){
        let helper = this;
        db.pool.getConnection(function(err, myCon) {
            if (err) {
                logger.error("Error while acquiring connection:" + err);
                return;
            }
            if (!myCon) {
                logger.error("Error while acquiring connection:");
                return;
            }
            let hourTime = Math.round((new Date().getTime() - 3600000)/1000);
            var cleanupQuery = "delete from performance where transferDate is NOT NULL and timestamp < "+hourTime+";";
            logger.info('cleanupQuery:'+cleanupQuery);
            myCon.query(cleanupQuery
                , function(err, results) {
                    error.handleConnectionError(err,myCon);
                    logger.info('Successfully cleaned up data');
                    myCon.release(function(err) {
                        if(err)logger.error("Error while closing connection:"+err);
                    });
                    setTimeout(function(){
                        helper.cleanup();
                    },30*60*1000);
                });
        })
    }
};
PerformanceHelper.cleanup();
module.exports = PerformanceHelper;
