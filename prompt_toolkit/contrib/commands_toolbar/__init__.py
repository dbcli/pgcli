
grammar = """
    # Ignore leading whitespace.
    .*

    # The command itself.
    (?P<command>[a-z-]+)

    # Any number between 0-8 parameters.
    (\s+ (?P<var1>[^\s]+)
        (\s+ (?P<var2>[^\s]+)
            (\s+ (?P<var3>[^\s]+)
                (\s+ (?P<var4>[^\s]+)
                    (\s+ (?P<var5>[^\s]+)
                        (\s+ (?P<var6>[^\s]+)
                            (\s+ (?P<var7>[^\s]+)
                                (\s+ (?P<var8>[^\s]+)?)
                            )?
                        )?
                    )?
                )?
            )?
        )?
    )?
    # Ignore trailing whitespace.
    .*
"""
