#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   main.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:15:20 by horarivo            #+#    #+#            #
#   Updated: 2026/09/09 11:59:57 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


import sys
from parser import Parser, ParseError

def main():
    try:
        parsed = Parser().parse(sys.argv[2])
    except (ParseError, OSError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)

if __name__=="__main__":
    main()
    