# op10
Python based code to look at patterns before and after earnings report dates for equities in the Dow 30 

This code analyzes historical trading data for the months/weeks/days leading up to, and immediately after, earnings reports are released.

It uses Zack's earnings surprise and sales surprise APIs and monitors shifts in the closign price of the stock based on whether it crosses
multiples or divisors of the opening price on the day its earnings report is released. I figured that because the Fibonacci sequence is
so prevalent in so many natural patterns, that looking at Fib multiples/divisors might prove useful. 

It's a work in progress, but so far the results are encouraging. 
