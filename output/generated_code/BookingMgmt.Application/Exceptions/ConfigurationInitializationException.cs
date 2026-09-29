using System;
using System.Runtime.Serialization;

namespace BookingMgmt.Application.Exceptions;

[Serializable]
public class ConfigurationInitializationException : Exception
{
    public ConfigurationInitializationException()
    {
    }

    public ConfigurationInitializationException(string message)
        : base(message)
    {
    }

    public ConfigurationInitializationException(string message, Exception innerException)
        : base(message, innerException)
    {
    }

#pragma warning disable SYSLIB0051 // Preserve legacy exception serialization compatibility where required.
    protected ConfigurationInitializationException(SerializationInfo info, StreamingContext context)
        : base(info, context)
    {
    }
#pragma warning restore SYSLIB0051
}
