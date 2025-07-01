Similariry Calibration
1. I want to understand (calibrate) how to interpret similarity scores
2. Create a very distinctive paragraph with specific details, dates, quantities & facts.
3. Write this to the vector database as our control document
4. Make a call to get related documents by asking for the control document
5. This should return the control document with a numerically very low similarity score, which means semantically similar
6. modify the control document so it is less like the original and make a call to get related docs.
7. This should return the original control document but with a numerically higher (less similar) similarity score
8. repeat this 4 more times and each time make the document less similar, call get related docs and remember the similarity score
9. based on all the similarity scores propose a similarity score that means the documents are no longer meaningfully related