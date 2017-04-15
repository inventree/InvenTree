from rest_framework.views import exception_handler


#class APIValidationError()

def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    #print(response)

    # Now add the HTTP status code to the response.
    if response is not None:

        data = {'error': response.data}
        response.data = data

    return response
