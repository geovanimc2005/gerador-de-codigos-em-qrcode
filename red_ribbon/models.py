from django.db import models

class MeuModelo(models.Model):
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.nome