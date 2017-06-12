***************
Error Responses
***************

When the REST API encounters a problem, or receives notification that the
validator has encountered a problem, it will notify clients with both an
appropriate HTTP status code, and a more detailed JSON response.


HTTP Status Codes
=================

.. list-table::
   :widths: 4, 16, 60
   :header-rows: 1

   * - Code
     - Title
     - Description
   * - 400
     - Bad Request
     - The request was malformed in some way, and will need to be modified
       before resubmitting. The accompanying JSON response will have more
       details.
   * - 404
     - Not Found
     - The request was well formed, but an identifier specified did not
       correspond to any resource in the validator. Returned by endpoints which
       fetch a single resource. Endpoints which return lists of resources will
       simply return an empty list.
   * - 500
     - Internal Server Error
     - Something is broken internally in the REST API or the validator. This may
       be a bug, and if reproducable, should be reported.
   * - 503
     - Service Unavailable
     - The REST API is unable to communicate with the validator. It may be down.
       You should try your request later.


JSON Response
=============

In the case of an error, rather than a *data* property, the JSON response will
include a single *error* property with three values:

   * *code* (integer) - a machine readable error code
   * *title* (string) - a short headline for the error
   * *message* (string) - a longer human readable description of what went wrong

.. note::

   While the title and message may change in the future, **the error code is
   fixed**, and will always refer to this particular problem.


Example JSON Response
---------------------

.. code-block:: json

   {
     "error": {
       "code": 1072,
       "title": "Record Not Found",
       "message": "There is no record with the id specified in global state."
     }
   }


Error Codes and Descriptions
============================

.. list-table::
   :widths: 4, 16, 60
   :header-rows: 1

   * - Code
     - Title
     - Description
   * - 10
     - Unknown Validator Error
     - An unknown error occurred with the validator while processing the
       request. This may be a bug, and if reproducable, should be reported.
   * - 15
     - Validator Not Ready
     - The validator has no genesis block, and so cannot be queried. Wait for
       genesis to be completed and resubmit. If you are running the validator,
       ensure it was set up properly.
   * - 17
     - Validator Timed Out
     - The request timed out while waiting for a response from the validator. It
       may not be running, or have encountered an internal error. The request
       may or may not have been processed.
   * - 18
     - Validator Disconnected
     - The validator sent a disconnect signal while processing the response, and
       is no longer available. Try your request again later.
   * - 20
     - Invalid Validator Response
     - The validator sent back a response which was not serialized properly
       and could not be decoded. There may be a problem with the validator.
   * - 21
     - Invalid Resource Header
     - The validator sent back a resource with a header that could not be
       decoded. There may be a problem with the validator, or the data may
       have been corrupted.
   * - 53
     - Invalid Count Query
     - The 'count' query parameter must be a positive, non-zero integer.
   * - 54
     - Invalid Paging Query
     - The validator rejected the paging request submitted. One or more of the
       'min', 'max', or 'count' query parameters were invalid or out of range.
   * - 66
     - Id Query Invalid or Missing
     - If using a GET request to fetch batch statuses, an 'id' query parameter
   * - 1071
     - Agent Not Found
     - There is no agent with the id specified in global state.
   * - 1072
     - Record Not Found
     - There is no record with the id specified in global state.
