# CodeHaircut

Give you codebase a haircut.

Have ever tried using a package that is 50MB+ in size? Do you REALLY need all that code?

CodeHaircut removes deadcode and unreachable code by analysing the execution trace when running your app. It rebuilds your dependencies to only contain code that you would use.

Realisitcally, this project is pretty useless in building usable code, in the current version, the rebuilt code is broken with syntax errors.

However, it was created to give developers a better understanding of how the packages they are using work internally. By removing large chunks of code that is meant for edge cases, developers have a much better reading experience, focusing only on code that will execute for specific to the use case of the developer.
