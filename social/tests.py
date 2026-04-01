from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Post


class SocialSecurityTests(TestCase):
	def setUp(self):
		self.alice = User.objects.create_user(username='alice', password='senha12345', email='alice@test.com')
		self.bob = User.objects.create_user(username='bob', password='senha12345', email='bob@test.com')
		self.eve = User.objects.create_user(username='eve', password='senha12345', email='eve@test.com')

		# alice e bob são amigos; eve é externa
		self.alice.perfil.amigos.add(self.bob)
		self.bob.perfil.amigos.add(self.alice)

	def test_conteudo_de_post_e_armazenado_criptografado(self):
		self.client.login(username='alice', password='senha12345')
		response = self.client.post(reverse('social:criar_post'), {
			'conteudo': 'segredo de teste',
			'visibilidade': 'publico',
		})
		self.assertEqual(response.status_code, 200)

		post = Post.objects.latest('id')
		self.assertNotEqual(post.conteudo, 'segredo de teste')
		self.assertEqual(post.conteudo_plano, 'segredo de teste')

	def test_post_amigos_nao_e_visivel_para_nao_amigo(self):
		post = Post(autor=self.alice, visibilidade=Post.VIS_AMIGOS)
		post.definir_conteudo('apenas amigos')
		post.save()

		self.client.login(username='eve', password='senha12345')
		response = self.client.get(reverse('social:listar_posts'), {
			'filtro': f'usuario_{self.alice.id}',
			'limite': 20,
			'offset': 0,
		})
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload['success'])
		self.assertEqual(len(payload['posts']), 0)

	def test_post_amigos_e_visivel_para_amigo(self):
		post = Post(autor=self.alice, visibilidade=Post.VIS_AMIGOS)
		post.definir_conteudo('somente rede de amizade')
		post.save()

		self.client.login(username='bob', password='senha12345')
		response = self.client.get(reverse('social:listar_posts'), {
			'filtro': f'usuario_{self.alice.id}',
			'limite': 20,
			'offset': 0,
		})
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload['success'])
		self.assertEqual(len(payload['posts']), 1)

	def test_comentario_em_post_privado_por_nao_amigo_retorna_403(self):
		post = Post(autor=self.alice, visibilidade=Post.VIS_AMIGOS)
		post.definir_conteudo('privado amigos')
		post.save()

		self.client.login(username='eve', password='senha12345')
		response = self.client.post(reverse('social:comentar_post', kwargs={'post_id': post.id}), {
			'conteudo': 'invasao',
		})
		self.assertEqual(response.status_code, 403)

	def test_envio_chat_para_nao_amigo_retorna_403(self):
		self.client.login(username='eve', password='senha12345')
		response = self.client.post(reverse('social:enviar_mensagem', kwargs={'username': 'alice'}), {
			'conteudo': 'oi sem permissao',
		})
		self.assertEqual(response.status_code, 403)
